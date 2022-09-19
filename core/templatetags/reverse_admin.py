from django import template
from django.urls import reverse

register = template.Library()


@register.filter
def reverse_admin(value):
    return reverse(
        'admin:%s_%s_change' % (value._meta.app_label, value._meta.model_name),
        args=(value.pk,),
    )
