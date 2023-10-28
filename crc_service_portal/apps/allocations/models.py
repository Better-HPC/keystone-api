from typing import cast

from django.contrib.auth import get_user_model
from django.db import models


class Cluster(models.Model):
    """A slurm cluster"""

    name = models.CharField(max_length=50)
    description = models.TextField(max_length=150, null=True, blank=True)
    enabled = models.BooleanField(default=True)

    def __str__(self) -> str:
        """Return the cluster name as a string"""

        return cast(str, self.name)


class Proposal(models.Model):
    """Project proposal requesting service unit allocations on one or more clusters"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    description = models.TextField(max_length=1600)
    submitted = models.DateField('Submission Date')
    approved = models.DateField('Approval Date', null=True, blank=True)

    def __str__(self) -> str:
        """Return the proposal title as a string"""

        return cast(str, self.title)


class Allocation(models.Model):
    """User service unit allocation"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    start = models.DateField('Start Date')
    expire = models.DateField('Expiration Date', null=True, blank=True)
    sus = models.IntegerField('Service Units')
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)

    def __str__(self) -> str:
        """Return a human-readable summary of the allocation"""

        if self.expire:
            date_range = f'starting {self.start}'

        else:
            date_range = f'from {self.start} to {self.expire}'

        return f'{self.cluster} allocation for {self.user} ({self.sus} SUs {date_range})'


class Publication(models.Model):
    """User submitted information for academic publication"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    abstract = models.TextField()
    date = models.DateField('Publication Date')
    journal = models.CharField(max_length=100, null=True, blank=True)
    doi = models.CharField(max_length=50, unique=True, null=True, blank=True)

    def get_truncated_title(self, max_length) -> str:
        """Return the publication title truncated to the given length and appended with ellipses

        Args:
            max_length: Maximum length of the returned string

        Return:
            The truncated publication title
        """

        ellipses = ' ...'
        title = str(self.title)

        # Truncate the title at the right most whitespace before the length limit
        if len(title) > max_length:
            title = title[:max_length - len(ellipses)].rsplit(' ', 1)[0] + ellipses

        return title

    def __str__(self) -> str:
        """Return the publication title truncated to 50 characters"""

        return self.get_truncated_title(50)


class Grant(models.Model):
    """Funding information for a PI grant"""

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)


class ProposalReview(models.Model):
    """Review feedback for a project proposal"""

    reviewer = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    approve = models.BooleanField()
    private_comments = models.CharField(max_length=500, null=True, blank=True)
    public_comments = models.CharField(max_length=500, null=True, blank=True)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    date_modified = models.DateTimeField(auto_now=True)
