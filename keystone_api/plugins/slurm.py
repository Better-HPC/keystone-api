"""Plugin providing wrappers around command line calls to a local Slurm installation"""

import logging
import re
from shlex import split
from subprocess import PIPE, Popen

log = logging.getLogger(__name__)

__all__ = [
    'get_cluster_limit',
    'get_cluster_usage',
    'get_slurm_account_names',
    'get_slurm_account_principal_investigator',
    'get_slurm_account_users',
    'set_cluster_limit',
]


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
