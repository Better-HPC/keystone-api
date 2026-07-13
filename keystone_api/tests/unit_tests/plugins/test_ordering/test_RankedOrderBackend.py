"""Unit tests for the `RankedOrderBackend` class."""

from types import SimpleNamespace

from django.db import connection, models
from django.test import TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from plugins.ordering import RankedOrderBackend


class OrderableRecord(models.Model):
    """Model backing the ordering backend tests."""

    class Meta:
        app_label = 'plugins'

    status = models.CharField(max_length=32)
    title = models.CharField(max_length=64)


def build_request(params: dict) -> Request:
    """Build a DRF request carrying the given query parameters."""

    return Request(APIRequestFactory().get('/', params))


class ParseTermMethod(TestCase):
    """Tests for the `parse_term` method."""

    def test_wellformed_term_parses_field_and_values(self) -> None:
        """Verify a well-formed term yields the field and its ordered values."""

        ranking = RankedOrderBackend.parse_term('status:urgent,normal,low')
        self.assertEqual(ranking.field, 'status')
        self.assertEqual(ranking.values, ('urgent', 'normal', 'low'))

    def test_surrounding_whitespace_stripped(self) -> None:
        """Verify surrounding whitespace is stripped before parsing."""

        ranking = RankedOrderBackend.parse_term('  status:urgent,normal  ')
        self.assertEqual(ranking.field, 'status')
        self.assertEqual(ranking.values, ('urgent', 'normal'))

    def test_empty_values_dropped(self) -> None:
        """Verify empty values between separators are dropped."""

        ranking = RankedOrderBackend.parse_term('status:a,,b')
        self.assertEqual(ranking.values, ('a', 'b'))

    def test_leading_dash_retained_in_field(self) -> None:
        """Verify a leading dash is retained in the field, not interpreted as direction."""

        ranking = RankedOrderBackend.parse_term('-status:a,b')
        self.assertEqual(ranking.field, '-status')

    def test_missing_colon_produces_no_ranking(self) -> None:
        """Verify a term with no separator produces no ranking."""

        self.assertIsNone(RankedOrderBackend.parse_term('statusurgent'))

    def test_missing_field_produces_no_ranking(self) -> None:
        """Verify a term with no field produces no ranking."""

        self.assertIsNone(RankedOrderBackend.parse_term(':a,b'))

    def test_missing_values_produces_no_ranking(self) -> None:
        """Verify a term with no values produces no ranking."""

        self.assertIsNone(RankedOrderBackend.parse_term('status:'))
        self.assertIsNone(RankedOrderBackend.parse_term('status:,,'))


class GetRankMapMethod(TestCase):
    """Tests for the `get_rank_map` method."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.backend = RankedOrderBackend()

    def test_multiple_terms_mapped_by_field(self) -> None:
        """Verify each requested field maps to its value ranking."""

        request = build_request({'_rank': ['status:urgent,normal', 'tier:gold,silver']})
        result = self.backend.get_rank_map(request)

        self.assertEqual(set(result), {'status', 'tier'})
        self.assertEqual(result['status'].values, ('urgent', 'normal'))

    def test_malformed_terms_silently_excluded(self) -> None:
        """Verify a malformed term produces no entry in the map."""

        request = build_request({'_rank': ['status:urgent,normal', 'garbage']})
        result = self.backend.get_rank_map(request)

        self.assertEqual(set(result), {'status'}, 'Malformed term should be excluded from the map')

    def test_duplicate_field_uses_last_term(self) -> None:
        """Verify a repeated field resolves to its last occurrence."""

        request = build_request({'_rank': ['status:a,b', 'status:c,d']})
        result = self.backend.get_rank_map(request)

        self.assertEqual(result['status'].values, ('c', 'd'), 'Last occurrence should win')

    def test_absent_parameter_yields_empty_map(self) -> None:
        """Verify an absent ranking parameter yields an empty map."""

        self.assertEqual(self.backend.get_rank_map(build_request({})), {})


class FilterQuerysetMethod(TestCase):
    """Tests for the `filter_queryset` method."""

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize a database table to test against."""

        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(OrderableRecord)

        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up temporary database tables."""

        super().tearDownClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(OrderableRecord)

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.backend = RankedOrderBackend()
        self.view = SimpleNamespace(ordering_fields='__all__')
        OrderableRecord.objects.bulk_create([
            OrderableRecord(status='urgent', title='alpha'),
            OrderableRecord(status='normal', title='bravo'),
            OrderableRecord(status='normal', title='alpha'),
            OrderableRecord(status='low', title='charlie'),
            OrderableRecord(status='pending', title='delta'),  # Unlisted status
        ])

    def build_queryset(self, params: dict, view: object = None) -> models.QuerySet:
        """Return the queryset ordered by the backend for the given parameters."""

        request = build_request(params)
        return self.backend.filter_queryset(request, OrderableRecord.objects.all(), view or self.view)

    def test_listed_values_ordered_by_rank(self) -> None:
        """Verify rows are ordered by list position rather than natural column order."""

        queryset = self.build_queryset({'_order': 'status', '_rank': 'status:urgent,normal,low'})
        statuses = list(queryset.values_list('status', flat=True))
        self.assertEqual(statuses, ['urgent', 'normal', 'normal', 'low', 'pending'])

    def test_unlisted_values_sorted_last(self) -> None:
        """Verify a value absent from the ranking sorts after all ranked values."""

        queryset = self.build_queryset({'_order': 'status', '_rank': 'status:urgent,normal,low'})
        statuses = list(queryset.values_list('status', flat=True))
        self.assertEqual(statuses[-1], 'pending', 'Unlisted value should sort last')

    def test_descending_reverses_rank(self) -> None:
        """Verify a descending order reverses the ranking and surfaces unlisted rows first."""

        queryset = self.build_queryset({'_order': '-status', '_rank': 'status:urgent,normal,low'})
        statuses = list(queryset.values_list('status', flat=True))
        self.assertEqual(statuses, ['pending', 'low', 'normal', 'normal', 'urgent'])

    def test_field_without_rank_uses_natural_order(self) -> None:
        """Verify a field with no matching ranking sorts by natural column order."""

        queryset = self.build_queryset({'_order': 'title'})
        titles = list(queryset.values_list('title', flat=True))
        self.assertEqual(titles, sorted(titles), 'Titles should be in natural ascending order')

    def test_multiple_order_levels_applied_in_sequence(self) -> None:
        """Verify a ranked field and a plain field combine as ordered sort levels."""

        queryset = self.build_queryset({'_order': 'status,title', '_rank': 'status:urgent,normal,low'})
        rows = list(queryset.values_list('status', 'title'))
        expected = [
            ('urgent', 'alpha'),
            ('normal', 'alpha'),
            ('normal', 'bravo'),
            ('low', 'charlie'),
            ('pending', 'delta'),
        ]
        self.assertEqual(rows, expected)

    def test_rank_without_matching_order_field_has_no_effect(self) -> None:
        """Verify a ranking for a field absent from the order produces no reordering."""

        with_rank = list(
            self.build_queryset({'_order': 'title', '_rank': 'status:urgent,normal,low'})
            .values_list('title', flat=True)
        )

        without_rank = list(self.build_queryset({'_order': 'title'}).values_list('title', flat=True))
        self.assertEqual(with_rank, without_rank, 'Unused ranking should not reorder rows')

    def test_disallowed_order_field_ignored(self) -> None:
        """Verify an order field outside the allowed set is ignored."""

        view = SimpleNamespace(ordering_fields=['status'])
        result = self.build_queryset({'_order': 'title'}, view=view)
        self.assertEqual(
            list(result.values_list('id', flat=True)),
            list(OrderableRecord.objects.values_list('id', flat=True)),
            'Disallowed field should leave the queryset order unchanged',
        )

    def test_no_ordering_returns_queryset_unchanged(self) -> None:
        """Verify the queryset is returned unchanged when no ordering is requested."""

        result = self.build_queryset({})
        self.assertEqual(
            list(result.values_list('id', flat=True)),
            list(OrderableRecord.objects.values_list('id', flat=True)),
        )


class GetSchemaOperationParametersMethod(TestCase):
    """Tests for the `get_schema_operation_parameters` method."""

    def setUp(self) -> None:
        """Create test fixtures using mock data."""

        self.backend = RankedOrderBackend()
        self.parameters = self.backend.get_schema_operation_parameters(SimpleNamespace())
        self.names = [parameter['name'] for parameter in self.parameters]

    def test_ordering_parameter_included(self) -> None:
        """Verify the inherited ordering parameter is documented."""

        self.assertIn(self.backend.ordering_param, self.names)

    def test_rank_parameter_included(self) -> None:
        """Verify the ranking parameter is documented under its configured name."""

        self.assertIn(self.backend.rank_param, self.names)

    def test_query_parameters_are_optional(self) -> None:
        """Verify query parameters are marked as optional."""

        for name in (self.backend.ordering_param, self.backend.rank_param):
            parameter = next(item for item in self.parameters if item['name'] == name)
            self.assertEqual(parameter['in'], 'query', f'Parameter {name} should be a query parameter')
            self.assertFalse(parameter['required'], f'Parameter {name} should be optional')
