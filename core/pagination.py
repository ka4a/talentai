from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination


class MultipleModelLimitPagination(LimitOffsetPagination):
    """
    For use with `drf_multiple_model` where `paginate_queryset` is
    called multiple times per call.
    """

    def paginate_queryset(self, queryset, request, view=None):
        result = super().paginate_queryset(queryset, request, view)

        try:
            self.total += self.count
        except AttributeError:
            self.total = self.count

        return result

    def format_response(self, data):
        return OrderedDict([('total', self.total), ('results', data)])
