"""Custom ordering backends for the Django REST Framework.

Ordering backends define the sequence in which records are returned from list
endpoints. This backend provides an `_order` parameter naming the fields to
sort by and an optional `_precedence` parameter assigning an explicit value
ranking to values in any ordered fields. A field named in `_order` with a
matching precedence is sorted by the listed precedence, while a field with
no precedence falls back to its natural column order.
"""

from dataclasses import dataclass

from django.db.models import Case, IntegerField, QuerySet, Value, When
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend
from rest_framework.request import Request
from rest_framework.views import APIView

__all__ = ['PrecedenceOrderingBackend', 'PrecedenceTerm']


@dataclass(frozen=True)
class PrecedenceTerm:
    """Ordering precedence for values of a single field."""

    field: str
    values: tuple[str, ...]


class PrecedenceOrderingBackend(BaseFilterBackend):
    """An ordering backend combining field ordering with per-field value precedence.

    Clients name the fields to sort by in the `_order` parameter, using a leading
    `-` for a descending order. The optional `_precedence` parameter assigns a
    ranking of field values as `field:value1,value2,value3` which is used to customize
    the sort order.
    """

    # The query parameter naming the fields to sort by.
    ordering_param: str = '_order'

    # The query parameter assigning an explicit value ranking to a field.
    precedence_param: str = '_precedence'

    def filter_queryset(self, request: Request, queryset: QuerySet, view: APIView) -> QuerySet:
        """Order the queryset by the requested fields, applying value precedence where defined.

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

        precedence = self.get_precedence_map(request)

        order_by = []
        for token in ordering:
            descending = token.startswith('-')
            field = token[1:] if descending else token

            if field in precedence:
                # Sort by the precedence rank annotation rather than the raw column
                annotation = f'_precedence_{field}'
                queryset = queryset.annotate(**{annotation: self.build_orm_case_expr(precedence[field])})
                field = annotation

            order_by.append(f'-{field}' if descending else field)

        return queryset.order_by(*order_by)

    def get_schema_operation_parameters(self, view: APIView) -> list[dict]:
        """Document the ordering and precedence query parameters in the OpenAPI schema.

        Args:
            view: The view the filter backend is attached to.

        Returns:
            The OpenAPI parameter definitions for the ordering query parameters.
        """

        return [
            {
                'name': self.ordering_param,
                'required': False,
                'in': 'query',
                'description': (
                    'Comma-separated fields to sort by. '
                    'Prefix a field with `-` for descending order.'
                ),
                'schema': {'type': 'string'},
            },
            {
                'name': self.precedence_param,
                'required': False,
                'in': 'query',
                'description': (
                    "Explicit ranking of a field's values as `field:value,value,value`. "
                    'Applied when the field also appears in the ordering parameter, with '
                    'unlisted values sorting last.'
                ),
                'schema': {'type': 'string'},
            },
        ]

    def get_ordering(self, request: Request, queryset: QuerySet, view: APIView) -> list[str]:
        """Return the validated ordering tokens from the request.

        Args:
            request: The incoming API request.
            queryset: The queryset being ordered.
            view: The view the filter backend is attached to.

        Returns:
            The requested ordering tokens, each optionally prefixed with `-`,
            limited to fields the view permits.
        """

        raw = request.query_params.get(self.ordering_param)
        if not raw:
            return []

        allowed = self.get_valid_fields(queryset, view)
        allow_any = allowed == '__all__'

        ordering = []
        for token in (value.strip() for value in raw.split(',')):
            field = token[1:] if token.startswith('-') else token
            if field and (allow_any or field in allowed):
                ordering.append(token)

        return ordering

    @staticmethod
    def get_valid_fields(queryset: QuerySet, view: APIView) -> list[str] | str:
        """Return the field names a client is permitted to order by.

        Defers to the view's `ordering_fields` when declared. When the view is
        silent, ordering falls back to the queryset model's concrete fields,
        matching the open field exposure of `AutoFilterBackend`.

        Args:
            queryset: The queryset being ordered.
            view: The view the filter backend is attached to.

        Returns:
            The allowed field names, or the string `'__all__'` for no restriction.
        """

        ordering_fields = getattr(view, 'ordering_fields', None)
        if ordering_fields is not None:
            return ordering_fields

        return [
            field.name
            for field in queryset.model._meta.get_fields()
            if getattr(field, 'concrete', False)
        ]

    def get_precedence_map(self, request: Request) -> dict[str, PrecedenceTerm]:
        """Map each requested field to its value precedence.

        Args:
            request: The incoming API request.

        Returns:
            A mapping from field name to its precedence term.
        """

        return {
            term.field: term
            for term in map(self.parse_term, request.query_params.getlist(self.precedence_param))
        }

    @staticmethod
    def parse_term(raw: str) -> PrecedenceTerm:
        """Parse a single raw query term into a precedence term.

        Args:
            raw: A raw `field:value,value` term.

        Returns:
            The parsed precedence term.

        Raises:
            ValidationError: The term is not of the form `field:value,value`.
        """

        field, separator, values = raw.strip().partition(':')
        parsed_values = tuple(value for value in values.split(',') if value)
        if not separator or not field or not parsed_values:
            raise ValidationError(f"Malformed precedence term: '{raw}'. Expected 'field:value,value'.")

        return PrecedenceTerm(field=field, values=parsed_values)

    @staticmethod
    def build_orm_case_expr(term: PrecedenceTerm) -> Case:
        """Build an ORM `Case` expression that ranks a field by value precedence.

        Args:
            term: The precedence term to rank by.

        Returns:
            A `Case` expression yielding each row's sort rank.
        """

        whens = [
            When(**{term.field: value}, then=Value(index))
            for index, value in enumerate(term.values)
        ]

        return Case(*whens, default=Value(len(term.values)), output_field=IntegerField())
