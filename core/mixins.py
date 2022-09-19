import warnings

from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from rest_framework.decorators import action
from rest_framework.response import Response


class ValidateModelMixin(object):
    """Validate a model instance."""

    @action(methods=['post'], detail=False)
    def validate_create(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return Response({})

    @action(methods=['post'], detail=False)
    def validate_partial_create(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.validate_create(request, *args, **kwargs)

    @action(methods=['post'], detail=True)
    def validate_update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        return Response({})

    @action(methods=['post'], detail=True)
    def validate_partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.validate_update(request, *args, **kwargs)
