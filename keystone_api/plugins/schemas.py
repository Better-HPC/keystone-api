"""Custom schema generation for DRF Spectacular.

Schema classes define how API endpoints are documented in the project's
OpenAPI specification. This includes determining how query parameters,
request bodies, and responses are rendered in the generated documentation.
"""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.openapi import AutoSchema
from rest_framework.filters import BaseFilterBackend

__all__ = ['FilterGetAutoSchema', 'mark_all_get_fields_required']


class FilterGetAutoSchema(AutoSchema):
    """Custom OpenApi schema generator that includes filter parameters on `GET` operations.

    By default, DRF Spectacular only includes filter parameters in the OpenAPI
    schema for list endpoints. This custom schema class extends the default
    behavior to include filter parameters on all GET endpoints, including
    detail and custom endpoints.
    """

    def get_filter_backends(self) -> list[BaseFilterBackend | DjangoFilterBackend]:
        """Return the view's filter backends for GET requests, and an empty list otherwise."""

        # The parent class returns an empty list for non-list actions
        # We override to return the view's filter backends for all `GET` operations
        if self.method == "GET":
            return getattr(self.view, 'filter_backends', [])

        return []


def _get_response_schema_names(result: dict) -> set[str]:
    """Collect all schema names referenced in GET response bodies.

    Args:
        result: The full OpenAPI schema dict from drf-spectacular.

    Returns:
        A set of schema component names referenced in any GET response body.
    """

    names = set()
    for path in result['paths'].values():
        operation = path.get('get', {})
        for response in operation.get('responses', {}).values():
            ref = (
                response
                .get('content', {})
                .get('application/json', {})
                .get('schema', {})
                .get('$ref', '')
            )
            if ref:
                names.add(ref.split('/')[-1])

    return names


def mark_all_get_fields_required(result: dict, generator, request, public) -> dict:
    """Mark all readable fields as required in GET response schemas.

    drf-spectacular marks response body fields as optional when they are
    nullable or have a model-level default. This hook corrects response
    schemas by marking every non-writeOnly field as required in `GET`
    responses, accurately reflecting that all readable fields are always
    present.

    Args:
        result: The full OpenAPI schema dict.
        generator: The drf-spectacular schema generator instance.
        request: The request that triggered schema generation, if any.
        public: Whether the schema is being generated for public consumption.

    Returns:
        The mutated OpenAPI schema dict with required fields corrected.
    """

    response_schema_names = _get_response_schema_names(result)

    for name, schema in result['components']['schemas'].items():
        if name not in response_schema_names:
            continue

        properties = schema.get('properties', {})
        schema['required'] = sorted(
            field_name
            for field_name, field_schema in properties.items()
            if not field_schema.get('writeOnly', False)
        )

    return result
