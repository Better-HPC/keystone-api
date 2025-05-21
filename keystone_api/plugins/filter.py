"""Extends the `django-filter` package with custom filter backends.

Filter backends define the default behavior when filtering database queries
for REST API calls based on URL parameters. This plugin customizes the default
filters available for different field types (e.g., char, int, bool, etc.).
"""

from django import views
from django.db import models
from django_filters.rest_framework import DjangoFilterBackend

__all__ = ['AdvancedFilterBackend', 'FactoryBuiltFilterSet']


class FactoryBuiltFilterSet:
    """A factory generated filterset class

    This is an empty class used for type checking/hinting.
    """


class AdvancedFilterBackend(DjangoFilterBackend):
    """Custom filter backend for Django REST framework

    This filter backend automatically generates filters for Django model fields based on their types.
    """

    _default_filters = ['exact', 'in', 'isnull']
    _numeric_filters = _default_filters + ['lt', 'lte', 'gt', 'gte']
    _text_filters = _default_filters + ['contains', 'startswith', 'endswith']
    _date_filters = _default_filters + _numeric_filters + ['year', 'month', 'day', 'week', 'week_day']
    _time_filters = _default_filters + _numeric_filters + ['hour', 'minute', 'second']

    _field_filter_map = {
        models.AutoField: _numeric_filters,
        models.BigAutoField: _numeric_filters,
        models.BigIntegerField: _numeric_filters,
        models.BooleanField: _default_filters,
        models.CharField: _text_filters,
        models.CommaSeparatedIntegerField: _default_filters,
        models.DateField: _date_filters,
        models.DateTimeField: list(set(_date_filters + _time_filters)),
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
    def field_filter_map(self) -> dict[type[models.Field], str]:
        return self._field_filter_map.copy()

    def get_filterset_class(self, view: views.View, queryset: models.Manager = None) -> type[FactoryBuiltFilterSet]:
        """Get the filterSet class for a given view

        Args:
            view: The view used to handel requests that will be filtered
            queryset: The queryset returning the data that will be filtered

        Returns:
            A FilterSet class
        """

        # Default to the user defined filterset class
        # The super class method returns `None` if not defined
        if filterset_class := super().get_filterset_class(view, queryset=queryset):
            return filterset_class

        # Map field names to a list of appropriate filters
        field_filters = dict()
        for field in queryset.model._meta.get_fields():
            if filters := self._field_filter_map.get(type(field), None):
                field_filters[field.name] = filters

        # Create a filterset class with the appropriate filters for each field
        class FactoryFilterSet(self.filterset_base, FactoryBuiltFilterSet):
            class Meta:
                model = queryset.model
                fields = field_filters

        return FactoryFilterSet
