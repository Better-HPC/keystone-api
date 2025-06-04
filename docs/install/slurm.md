# Configuring Slurm

Slurm categorizes system usage in terms of trackable resources (TRES).
Keystone uses these TRES values to enforce allocation limits in the Slurm scheduler.
The total billable TRES for a given Slurm job is calculated as a weighted sum of usage $\left ( U \right )$, 
scaled by administrator-defined billing weights $\left ( W \right )$ :

$$ 
\text{Billable Usage} = \sum_\text{TRES} \,\, \left ( W_\text{TRES} * U_\text{TRES} \right )
$$

Keystone interfaces with Slurm to automatically enforce per-cluster limits on a group's total allowed *Billable Usage*.
These limits are enforced using the `GrpTresMins=billing=[LIMIT]` setting.
Once a group reaches its allocation limit, additional Slurm jobs will be prevented from running on the target cluster.

Keystone is agnostic to most Slurm settings and requires minimal modification to an existing cluster.
However, certain fairshare features are incompatible with Keystone's accounting model and must be disabled.
The steps below outline the configuration required for integration with Slurm.

## Enable Resource Tracking

To impose usage limits, Keystone requires the utilized resource to be represented as a TRES in Slurm.
Tracking is enabled by default for common resources such as CPU, memory, and energy.
Administrators may extend this list to include additional resource types, such as GPUs.

The `AccountingStorageTRES` setting is used to configure which TRES values are stored in the Slurm database.
Refer to the official [Surm documentation](https://slurm.schedmd.com/tres.html#conf) for more details.

??? Example "Example: Tracking GPU usage"

    To enable tracking for GPU resources:

    ```
    AccountingStorageTRES=gres/gpu
    ```

??? Example "Example: Tracking GPU and IOP"

    To track GPU and a license-based resource named `iop1`:

    ```
    AccountingStorageTRES=gres/gpu,license/iop1
    ```

## Disable Usage Decay

Slurm defaults to using the [multifactor priority plugin](https://slurm.schedmd.com/priority_multifactor.html) to schedule jobs.
To verify this, inspect the PriorityType setting:

```bash
scontrol show config | grep PriorityType
```

When using the multifactor plugin, the `PriorityDecayHalfLife` and `PriorityUsageResetPeriod` settings need to be disabled.
These settings cause Slurm to reduce recorded usage over time, which interferes with Keystone's accounting calculations.

```
PriorityDecayHalfLife=00:00:00
PriorityUsageResetPeriod=NONE
```

!!! Important

    Disabling these settings may affect your Slurm fairshare policy.  
    Administrators are strongly encouraged to review their fairshair policy settings. 

## Configure Charging Rates

TRES billing weights default to zero and must be explicitly defined using the `TRESBillingWeights` option.
Weights are set per partition and can be expressed in a variety of units.
See the [Slurm documentation](https://slurm.schedmd.com/tres.html) for full details.

??? Example "Example: Billing for CPU"

    To only charge users for CPU usage:

    ```
    PartitionName=partition_name TRESBillingWeights="CPU=1.0"
    ```

??? Example "Example: Billing for CPU and GPU"

    To charge GPU usage at twice the rate of CPU usage:

    ```
    PartitionName=partition_name TRESBillingWeights="CPU=1.0,GRES/gpu=2.0"
    ```

To ensure accurate usage calculations, enable the `MAX_TRES` flag in the `PriorityFlags` setting.
This ensures the billable TRES includes node-local resources (e.g. CPU, memory, GPU) as well as global TRES (e.g. licenses).

```
PriorityFlags=MAX_TRES
```
