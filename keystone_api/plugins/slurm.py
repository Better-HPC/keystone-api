"""Plugin providing wrappers around command line calls to a local Slurm installation"""

import logging
import re
from datetime import datetime, timedelta
from shlex import split
from subprocess import PIPE, Popen

log = logging.getLogger(__name__)

__all__ = [
    'get_cluster_jobs',
    'get_cluster_limit',
    'set_cluster_limit',
    'get_cluster_usage',
    'get_slurm_account_names',
    'get_slurm_account_principal_investigator',
    'get_slurm_account_users',
    'parse_slurm_date',
    'parse_slurm_elapsed'
]


def parse_slurm_date(date_str: str) -> datetime | None:
    """Convert a slurm datetime string into a `datetime` object.

    Args:
        date_str: The value to convert.

    Returns:
        The `datetime` object or `None` if the value fails to parse.
    """

    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S").astimezone()

    except (ValueError, Exception):
        log.error(f'Invalid slurm datetime: {date_str}')
        return None


def parse_slurm_elapsed(elapsed_str: str) -> timedelta | None:
    """Convert a slurm time string into a `timedelta` object.

    Args:
        elapsed_str: The value to convert.

    Returns:
        The `timedelta` object or `None` if the value fails to parse.
    """

    try:
        if '-' in elapsed_str:
            days_part, time_part = elapsed_str.split('-')
            days = int(days_part)

        else:
            days = 0
            time_part = elapsed_str

        parts = list(map(int, time_part.split(':')))

        if len(parts) == 3:
            hours, minutes, seconds = parts

        elif len(parts) == 2:
            hours, minutes = parts
            seconds = 0

        else:
            raise ValueError

        return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    except (ValueError, Exception):
        log.error(f'Invalid slurm duration: {elapsed_str}')
        return None


def subprocess_call(args: list[str]) -> str:
    """Wrapper method for executing shell commands via ``Popen.communicate``

    Args:
        args: A sequence of program arguments

    Returns:
        The piped output to STDOUT
    """

    process = Popen(args, stdout=PIPE, stderr=PIPE)
    out, err = process.communicate()

    if process.returncode != 0:
        message = f"Error executing shell command: {' '.join(args)} \n {err.decode('utf-8').strip()}"
        log.error(message)
        raise RuntimeError(message)

    return out.decode("utf-8").strip()


def get_slurm_account_names(cluster_name: str | None = None) -> set[str]:
    """Return a list of Slurm account names from `sacctmgr`

    Args:
        cluster_name: Optionally return account names on a specific Slurm cluster

    Returns:
        A set of unique Slurm account names
    """

    cmd = split("sacctmgr show -nP account withassoc where parents=root format=Account")
    if cluster_name:
        cmd.append(f"cluster={cluster_name}")

    return set(subprocess_call(cmd).split())


def get_slurm_account_principal_investigator(account_name: str) -> str:
    """Return the Principal Investigator (PI) username (Slurm account description field) for a Slurm account given the
    account name

    Args:
        account_name: The Slurm account name

    Returns:
        The Slurm account PI username (description field)
    """

    cmd = split(f"sacctmgr show -nP account where account={account_name} format=Descr")
    return subprocess_call(cmd)


def get_slurm_account_users(account_name: str, cluster_name: str | None = None) -> set[str]:
    """Return all usernames tied to a Slurm account

    Args:
        account_name: The Slurm account name
        cluster_name: Optionally provide the name of the cluster to get usernames on

    Returns:
        The account owner username
    """

    cmd = split(f"sacctmgr show -nP association where account={account_name} format=user")
    if cluster_name:
        cmd.append(f"cluster={cluster_name}")

    return set(subprocess_call(cmd).split())


def set_cluster_limit(account_name: str, cluster_name: str, limit: int) -> None:
    """Update the TRES Billing usage limit for a given Slurm account and cluster

    The default expected limit unit is Hours, and a conversion takes place as Slurm uses minutes.

    Args:
        account_name: The name of the Slurm account
        cluster_name: The name of the Slurm cluster
        limit: The new TRES usage limit in hours
    """

    limit *= 60  # Convert the input hours to minutes
    cmd = split(f"sacctmgr modify -i account where account={account_name} cluster={cluster_name} set GrpTresMins=billing={limit}")
    subprocess_call(cmd)


def get_cluster_limit(account_name: str, cluster_name: str) -> int:
    """Return the current TRES Billing usage limit for a given Slurm account and cluster

    The limit unit coming out of Slurm is minutes, and the default behavior is to convert this to hours.
    This can be skipped with in_hours = False.

    Args:
        account_name: The name of the Slurm account
        cluster_name: The name of the Slurm cluster

    Returns:
        The current TRES Billing usage limit in hours
    """

    cmd = split(f"sacctmgr show -nP association where account={account_name} cluster={cluster_name} format=GrpTRESMins")

    try:
        limit = re.findall(r'billing=(.*)', subprocess_call(cmd))[0]

    except IndexError:
        log.debug(f"'billing' limit not found in command output from {cmd}, assuming zero for current limit")
        return 0

    limit = int(limit) if limit.isnumeric() else 0
    return limit // 60  # convert from minutes to hours


def get_cluster_usage(account_name: str, cluster_name: str) -> int:
    """Return the total billable usage in hours for a given Slurm account

    Args:
        account_name: The name of the account to get usage for
        cluster_name: The name of the cluster to get usage on

    Returns:
        An integer representing the total (historical + current) billing TRES hours usage from sshare
    """

    cmd = split(f"sshare -nP -A {account_name} -M {cluster_name} --format=GrpTRESRaw")

    try:
        usage = re.findall(r'billing=(.*),fs', subprocess_call(cmd))[0]

    except IndexError:
        log.debug(f"'billing' usage not found in command output from {cmd}, assuming zero for current usage")
        return 0

    usage = int(usage) if usage.isnumeric() else 0
    return usage // 60  # convert from minutes to hours


def get_cluster_jobs(cluster_name: str) -> list[dict]:
    """Retrieve SLURM job information for a given cluster.

    Args:
        cluster_name: Name of the SLURM cluster to query jobs for.

    Returns:
        A list of dictionaries, each containing metadata for a different job.
    """

    # Field names to fetch from slurm and their returned order
    fields = (
        "Account", "AllocNodes", "AllocTres", "DerivedExitCode", "Elapsed",
        "End", "Group", "JobId", "JobName", "NodeList", "Priority",
        "Partition", "QOS", "Start", "State", "Submit", "User"
    )

    cmd = split(
        f"sacct --allusers --allocations --noheader --parsable2 "
        f"--clusters={cluster_name} --format={','.join(fields)}"
    )

    job_list = []
    for line in subprocess_call(cmd).splitlines():
        parsed_line = line.split('|')
        job_data: dict[str, any] = {field.lower(): value for field, value in zip(fields, parsed_line)}

        # Cast select values into Python objects
        job_data['priority'] = int(job_data['priority']) if job_data['priority'] else None
        job_data['submit'] = parse_slurm_date(job_data['submit'])
        job_data['start'] = parse_slurm_date(job_data['start'])
        job_data['end'] = parse_slurm_date(job_data['end'])
        job_data['elapsed'] = parse_slurm_elapsed(job_data['elapsed'])

        job_list.append(job_data)

    return job_list
