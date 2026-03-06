"""Unit tests for the `FilterDefinition` class."""

from django.db import models
from django.test import TestCase
from django_filters import rest_framework as filters

from plugins.filters import FilterDefinition


class SampleModel(models.Model):
    """Sample database model for testing"""

    class Meta:
        app_label = 'test_FilterDefinition'

    char_field = models.CharField(max_length=100)
    integer_field = models.IntegerField()
    foreign_key_field = models.ForeignKey('self', on_delete=models.CASCADE, null=True)


class ParamNameMethod(TestCase):
    """Test query parameter name generation via the `param_name` method."""

    def test_default_suffix_uses_expr(self) -> None:
        """Verify the lookup expression is used as the suffix by default."""

        definition = FilterDefinition("contains")
        result = definition.param_name("title")
        self.assertEqual(result, "title__contains")

    def test_custom_suffix(self) -> None:
        """Verify a custom suffix overrides the lookup expression."""

        definition = FilterDefinition("in", suffix="not_in")
        result = definition.param_name("status")
        self.assertEqual(result, "status__not_in")

    def test_none_suffix_returns_bare_field_name(self) -> None:
        """Verify a `None` suffix returns the field name with no suffix."""

        definition = FilterDefinition("exact", suffix=None)
        result = definition.param_name("name")
        self.assertEqual(result, "name")

    def test_different_expressions_produce_different_names(self) -> None:
        """Verify distinct expressions on the same field yield distinct parameter names."""

        field_name = "age"
        lt_def = FilterDefinition("lt")
        gte_def = FilterDefinition("gte")

        self.assertNotEqual(
            lt_def.param_name(field_name),
            gte_def.param_name(field_name),
            'Different expressions produced the same parameter name',
        )


class ToFilterMethod(TestCase):
    """Test `Filter` instance creation via the `to_filter` method."""

    def _get_model_field(self, field_name: str) -> models.Field:
        """Retrieve a field instance from `SampleModel` by name."""

        return SampleModel._meta.get_field(field_name)

    def test_returns_filter_instance(self) -> None:
        """Verify the return value is a `Filter` instance."""

        definition = FilterDefinition("exact", suffix=None)
        result = definition.to_filter(self._get_model_field("char_field"))
        self.assertIsInstance(result, filters.Filter)

    def test_lookup_expression_is_set(self) -> None:
        """Verify the filter uses the correct ORM lookup expression."""

        definition = FilterDefinition("contains")
        result = definition.to_filter(self._get_model_field("char_field"))
        self.assertEqual(result.lookup_expr, "contains")

    def test_negate_false_by_default(self) -> None:
        """Verify filters are not negated by default."""

        definition = FilterDefinition("exact", suffix=None)
        result = definition.to_filter(self._get_model_field("char_field"))
        self.assertFalse(result.exclude, 'Filter is negated when negate was not set')

    def test_negate_sets_exclude(self) -> None:
        """Verify a negated definition produces an excluding filter."""

        definition = FilterDefinition("contains", negate=True, suffix="not_contains")
        result = definition.to_filter(self._get_model_field("char_field"))
        self.assertTrue(result.exclude, 'Filter is not negated when negate was set')

    def test_in_lookup_wraps_with_base_in_filter(self) -> None:
        """Verify `in` lookups produce a filter that inherits from `BaseInFilter`."""

        definition = FilterDefinition("in")
        result = definition.to_filter(self._get_model_field("integer_field"))
        self.assertIsInstance(result, filters.BaseInFilter)

    def test_in_lookup_preserves_negation(self) -> None:
        """Verify negation is preserved when wrapping with `BaseInFilter`."""

        definition = FilterDefinition("in", negate=True, suffix="not_in")
        result = definition.to_filter(self._get_model_field("integer_field"))
        self.assertIsInstance(result, filters.BaseInFilter)
        self.assertTrue(result.exclude, 'Negation was lost during BaseInFilter wrapping')

    def test_in_lookup_preserves_field_name(self) -> None:
        """Verify the field name is preserved when wrapping with `BaseInFilter`."""

        definition = FilterDefinition("in")
        result = definition.to_filter(self._get_model_field("integer_field"))
        self.assertEqual(result.field_name, "integer_field")

    def test_non_in_lookup_does_not_wrap(self) -> None:
        """Verify non-`in` lookups are not wrapped with `BaseInFilter`."""

        definition = FilterDefinition("gte")
        result = definition.to_filter(self._get_model_field("integer_field"))
        self.assertNotIsInstance(result, filters.BaseInFilter)

    def test_resolves_correct_filter_class_for_field_type(self) -> None:
        """Verify different filter classes are resolved for different field types."""

        definition = FilterDefinition("exact", suffix=None)
        char_filter = definition.to_filter(self._get_model_field("char_field"))
        int_filter = definition.to_filter(self._get_model_field("integer_field"))

        self.assertNotEqual(
            type(char_filter),
            type(int_filter),
            'Different field types resolved to the same filter class',
        )
