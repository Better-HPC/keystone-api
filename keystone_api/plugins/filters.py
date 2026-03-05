"""Custom filter backends for the Django REST Framework.

Filter backends define how query parameters are handled in API requests.
This includes assigning parameters to endpoints, parsing values from incoming
requests, and applying parsed values in ORM queries.
"""

from dataclasses import dataclass

from django import views
from django.db import models
from django_filters import rest_framework as filters

__all__ = ['AdvancedFilterBackend', 'FactoryBuiltFilterSet', 'FilterExpression']


@dataclass(frozen=True)
class FilterExpression:
    """Defines a filter lookup expression and its behavior.

    Attributes:
        expr: The ORM lookup expression (e.g., "exact", "contains", "in")
        negate: Whether to generate a negated (exclude) filter instead of a standard one
        param: The suffix used in the query parameter name. Defaults to `expr` if not provided.
    """

    expr: str
    negate: bool = False
    param: str = ""

    def __post_init__(self) -> None:
        if not self.param:
            object.__setattr__(self, 'param', self.expr)

    def to_filter(self, field: models.Field) -> filters.Filter | None:
        """Create a django-filter Filter instance for a given model field.

        Uses django-filter's built-in field resolution to determine the
        appropriate filter class, then applies negation and list-wrapping
        as needed.

        Args:
            field: The Django model field to create a filter for

        Returns:
            A configured Filter instance
        """

        # Create a filter for the specific database field type
        filt = filters.FilterSet.filter_for_field(field, field.name, self.expr)
        filt.exclude = self.negate

        # Wrap in BaseInFilter for list-based lookups
        if self.expr == "in" and filters.BaseInFilter not in type(filt).__mro__:
            wrapped_class = type(
                f"BaseIn{type(filt).__name__}",
                (filters.BaseInFilter, type(filt)),
                {},
            )

            filt = wrapped_class(
                field_name=filt.field_name,
                lookup_expr=filt.lookup_expr,
                exclude=filt.exclude,
            )

        return filt


class FactoryBuiltFilterSet:
    """A factory generated filterset class

    This is an empty base class used to enable type checking/hinting
    on dynamically generated subclasses.
    """


class AdvancedFilterBackend(filters.DjangoFilterBackend):
    """Dynamic filter backend for model based ViewSets.

    Automatically generates query parameters for model based viewsets based
    on the underlying model fields (e.g., comparison operators for numeric
    fields, pattern matching for text fields).
    """

    _default_filters = [
        FilterExpression("exact"),
        FilterExpression("in"),
        FilterExpression("in", negate=True, param="not_in"),
        FilterExpression("isnull"),
        FilterExpression("isnull", negate=True, param="not_isnull"),
    ]

    _numeric_filters = _default_filters + [
        FilterExpression("lt"),
        FilterExpression("lte"),
        FilterExpression("gt"),
        FilterExpression("gte"),
    ]

    _text_filters = _default_filters + [
        FilterExpression("contains"),
        FilterExpression("contains", negate=True, param="not_contains"),
        FilterExpression("startswith"),
        FilterExpression("endswith"),
    ]

    _date_filters = _numeric_filters + [
        FilterExpression("year"),
        FilterExpression("month"),
        FilterExpression("day"),
        FilterExpression("week"),
        FilterExpression("week_day"),
    ]

    _time_filters = _numeric_filters + [
        FilterExpression("hour"),
        FilterExpression("minute"),
        FilterExpression("second"),
    ]

    _date_time_filters = _numeric_filters + [
        FilterExpression("year"),
        FilterExpression("month"),
        FilterExpression("day"),
        FilterExpression("week"),
        FilterExpression("week_day"),
        FilterExpression("hour"),
        FilterExpression("minute"),
        FilterExpression("second"),
    ]

    _field_filter_map: dict[type[models.Field], list[FilterExpression]] = {
        models.AutoField: _numeric_filters,
        models.BigAutoField: _numeric_filters,
        models.BigIntegerField: _numeric_filters,
        models.BooleanField: _default_filters,
        models.CharField: _text_filters,
        models.CommaSeparatedIntegerField: _default_filters,
        models.DateField: _date_filters,
        models.DateTimeField: _date_time_filters,
        models.DecimalField: _numeric_filters,
        models.DurationField: _default_filters,
        models.EmailField: _text_filters,
        models.FilePathField: _text_filters,
        models.FloatField: _numeric_filters,
        models.ForeignKey: _default_filters,
        models.GenericIPAddressField: _default_filters,
        models.IPAddressField: _default_filters,
        models.IntegerField: _numeric_filters,
        models.NullBooleanField: _default_filters,
        models.PositiveBigIntegerField: _numeric_filters,
        models.PositiveIntegerField: _numeric_filters,
        models.PositiveSmallIntegerField: _numeric_filters,
        models.SlugField: _text_filters,
        models.SmallAutoField: _numeric_filters,
        models.SmallIntegerField: _numeric_filters,
        models.TextField: _text_filters,
        models.TimeField: _time_filters,
        models.URLField: _text_filters,
        models.UUIDField: _default_filters,
    }

    @property
    def field_filter_map(self) -> dict[type[models.Field], list[FilterExpression]]:
        """A mapping of database field types to their corresponding filter definitions."""

        return self._field_filter_map.copy()

    def _build_filter_attrs(self, model: type[models.Model]) -> dict[str, filters.Filter]:
        """Build a dictionary of filter instances for all fields on a model.

        Args:
            model: The Django model class to generate filters for

        Returns:
            A dictionary mapping query parameter names to filter instances
        """

        attrs = {}
        for field in model._meta.get_fields():
            field_type = type(field)
            for filter_expression in self._field_filter_map.get(field_type, []):
                attrs[f"{field.name}__{filter_expression.param}"] = filter_expression.to_filter(field)

        return attrs

    def get_filterset_class(self, view: views.View, queryset: models.Manager = None) -> type[filters.FilterSet]:
        """Get the FilterSet class for a given view.

        If the view defines a custom filterset class, that class is used.
        Otherwise, a FilterSet is dynamically generated with standard and
        negated filters for every supported model field.

        Args:
            view: The view used to handle requests that will be filtered
            queryset: The queryset returning the data that will be filtered

        Returns:
            A FilterSet class
        """

        # Default to the user defined filterset class
        # The super class method returns `None` if not defined
        if filterset_class := super().get_filterset_class(view, queryset=queryset):
            return filterset_class

        # Build all filter instances
        attrs = self._build_filter_attrs(queryset.model)

        # Attach a Meta class with the model reference
        # `fields` is empty because filters are defined explicitly as attributes
        attrs['Meta'] = type('Meta', (), {'model': queryset.model, 'fields': []})

        # Dynamically construct the FilterSet class
        return type('FactoryFilterSet', (self.filterset_base, FactoryBuiltFilterSet), attrs)
