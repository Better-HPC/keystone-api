"""Unit tests for the `Grant` class."""

from django.test import TestCase

from apps.research_products.models import Grant


class IsoCurrencyTests(TestCase):
    """Test the dynamic population of currency definitions."""

    def test_common_currencies(self) -> None:
        """Verify common ISO currencies are defined with the correct labels."""

        self.assertEqual(Grant.IsoCurrency.USD, "USD")
        self.assertEqual(Grant.IsoCurrency.USD.label, "US Dollar")

        self.assertEqual(Grant.IsoCurrency.EUR, "EUR")
        self.assertEqual(Grant.IsoCurrency.EUR.label, "Euro")

        self.assertEqual(Grant.IsoCurrency.JPY, "JPY")
        self.assertEqual(Grant.IsoCurrency.JPY.label, "Yen")
