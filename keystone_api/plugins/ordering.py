"""Custom ordering backends for the Django REST Framework.

Ordering backends define the sequence in which records are returned from list
endpoints. This backend extends the default ordering behavior with an optional
`_rank` parameter used to assign an explicit ordering to a field's values. A
field named in the ordering parameter with a matching value ranking is sorted
by that ranking, while a field with no ranking falls back to its natural
column order.
"""

from dataclasses import dataclass

from django.db.models import Case, IntegerField, QuerySet, Value, When
from rest_framework.filters import OrderingFilter
from rest_framework.request import Request
from rest_framework.views import APIView

__all__ = ["RankedOrderBackend"]


@dataclass(frozen=True)
class ValueRanking:
    """An explicit ordering for the values of a single field."""

    field: str
    values: tuple[str, ...]


class RankedOrderBackend(OrderingFilter):
    """An ordering backend combining field ordering with per-field value ranking.

    Clients name the fields to sort by in the `_order` parameter, using a leading
    `-` for a descending order. The optional `_rank` parameter assigns a ranking
    of field values as `field:value1,value2,value3`, customizing the resulting
    sort order.
    """

    # The query parameter containing field names to sort by.
    ordering_param: str = "_order"

    # The query parameter containing an optional value ranking for a field.
    rank_param: str = "_rank"

    def filter_queryset(self, request: Request, queryset: QuerySet, view: APIView) -> QuerySet:
        """Order a given queryset by the requested fields, applying value rankings where defined.

        Args:
            request: The incoming API request.
            queryset: The queryset to be ordered.
            view: The view the filter backend is attached to.

        Returns:
            The queryset ordered by the requested fields.
        """

        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset

        rankings = self.get_rank_map(request)

        order_by = []
        for token in ordering:
            descending = token.startswith("-")
            field = token[1:] if descending else token

            if field in rankings:
                # Sort by the value rank annotation rather than the raw column
                annotation = f"_rank_{field}"
                queryset = queryset.annotate(**{annotation: self.build_orm_case_expr(rankings[field])})
                field = annotation

            order_by.append(f"-{field}" if descending else field)

        return queryset.order_by(*order_by)

    def get_schema_operation_parameters(self, view: APIView) -> list[dict]:
        """Document query parameters in the OpenAPI schema.

        Args:
            view: The view the filter backend is attached to.

        Returns:
            The OpenAPI parameter definitions for the ordering query parameters.
        """

        return super().get_schema_operation_parameters(view) + [
            {
                "name": self.rank_param,
                "required": False,
                "in": "query",
                "description": (
                    "Explicit ranking of a field's values as `field:value,value,value`. "
                    "Applied when the field also appears in the ordering parameter, with "
                    "unlisted values sorting last."
                ),
                "schema": {"type": "string"},
            },
        ]

    def get_rank_map(self, request: Request) -> dict[str, ValueRanking]:
        """Map each requested field to its value ranking.

        Malformed terms are silently ignored.

        Args:
            request: The incoming API request.

        Returns:
            A mapping from field name to its value ranking.
        """

        return {
            ranking.field: ranking
            for ranking in map(self.parse_term, request.query_params.getlist(self.rank_param))
            if ranking is not None
        }

    @staticmethod
    def parse_term(raw: str) -> ValueRanking | None:
        """Parse a single raw query term into a value ranking.

        Args:
            raw: A raw `field:value,value` term.

        Returns:
            The parsed value ranking, or `None` when the term is malformed.
        """

        field, separator, values = raw.strip().partition(":")
        parsed_values = tuple(value for value in values.split(",") if value)
        if not separator or not field or not parsed_values:
            return None

        return ValueRanking(field=field, values=parsed_values)

    @staticmethod
    def build_orm_case_expr(ranking: ValueRanking) -> Case:
        """Build an ORM `Case` expression ranking a field by an explicit value order.

        Args:
            ranking: The value ranking to apply.

        Returns:
            A `Case` expression yielding each row's sort rank.
        """

        whens = [
            When(**{ranking.field: value}, then=Value(index))
            for index, value in enumerate(ranking.values)
        ]

        return Case(*whens, default=Value(len(ranking.values)), output_field=IntegerField())
