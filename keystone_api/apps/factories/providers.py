"""Providers for shared instances across clusters.

Provider classes are used to provide seeded providers such as Faker and random.
"""

import random
from faker import Faker

class SeededProvider:
    """A provider class that shares seeded Faker and random instances."""

    def __init__(self, seed=None):
        """Initialize with an optional seed for reproducibility."""
        self._fake = Faker()
        if seed is not None:
            Faker.seed(seed)
            self._random = random.Random(seed)
            self._fake.seed_instance(seed)

    @property
    def random(self):
        return self._random

    @property
    def fake(self):
        return self._fake

    def reconfigure(self, seed=42):
        """Reconfigure the provider with a new seed."""
        Faker.seed(seed)
        self._random = random.Random(seed)
        self._fake.seed_instance(seed)

# Global instance of the provider
global_provider = SeededProvider()
