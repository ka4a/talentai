import re
from collections import OrderedDict
from contextlib import contextmanager

from django.db.models import F
from djangorestframework_camel_case.util import camel_to_underscore
from rest_framework.filters import OrderingFilter


@contextmanager
def unlock_request_query_params(request):
    """Make request QueryDict mutable for a short amount of time."""
    mutable_state = request.query_params._mutable
    request.query_params._mutable = True
    yield None
    request.query_params._mutable = mutable_state


def mutate_ordering_fields(value, mapping):
    """Replace ordering values according to mapping."""
    matches = re.search(r'^[+-]', value)
    symb = matches[0] if matches else ''
    value = value.replace(symb, '')

    if value not in mapping:
        return symb + value

    return ','.join(symb + str(m) for m in mapping[value])


class CamelCaseOrderingFilter(OrderingFilter):
    """Class to allow camel case parameters in ordering."""

    def get_ordering(self, request, queryset, view):
        """Update ordering request query params values.

        Translate ordering camelCase values to snake_case. Also apply
        ordering_filed_mappings to allow order by non-model fields.
        """
        ordering_mapping = getattr(view, 'ordering_fields_mapping', {})
        ordering = request.query_params.get('ordering', '')

        if ordering:
            with unlock_request_query_params(request):
                ordering = ','.join(
                    list(
                        OrderedDict.fromkeys(
                            mutate_ordering_fields(f, ordering_mapping)
                            for f in camel_to_underscore(ordering).split(',')
                        )
                    )
                )
                request.query_params['ordering'] = ordering

        return super().get_ordering(request, queryset, view)

    def filter_queryset(self, request, queryset, view):
        """Override to sort nulls last by default."""
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            ordering_args = []
            for i in ordering:
                is_desc = i.startswith('-')
                field_name = i[1:] if is_desc else i

                if is_desc:
                    ordering_args.append(F(field_name).desc(nulls_last=True))
                else:
                    ordering_args.append(F(field_name).asc(nulls_first=True))

            return queryset.order_by(*ordering_args)

        return queryset
