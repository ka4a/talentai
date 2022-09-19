# Replace null values by empty string
# Find duplicated candidates, reset their unique values to empty values
# and set original field
from django.db import migrations
from django.db.models import Count, Q


def update_unique_fields(dupes, field_name, candidates):
    for entry in dupes:
        field_value = entry[field_name]
        duplicates = candidates.filter(**{field_name: field_value}).order_by(
            'created_at'
        )

        original_candidate = duplicates[0]

        for candidate in duplicates[1:]:
            setattr(candidate, field_name, '')
            setattr(candidate, 'original', original_candidate)
            candidate.save()


def apply_unique_fields(apps, schema_editor):
    Candidate = apps.get_model('core', 'Candidate')

    candidates = Candidate.objects.filter(archived=False)

    dupes = dict()

    dupes['email'] = (
        candidates.values('email')
        .annotate(Count('id'))
        .order_by()
        .filter(Q(id__count__gt=1) & ~Q(email='') & ~Q(email=None))
    )

    dupes['secondary_email'] = (
        candidates.values('secondary_email')
        .annotate(Count('id'))
        .order_by()
        .filter(Q(id__count__gt=1) & ~Q(secondary_email='') & ~Q(secondary_email=None))
    )

    for field_name, queryset in dupes.items():
        update_unique_fields(queryset, field_name, candidates)


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0135_candidate_is_client_contact'),
    ]

    operations = [migrations.RunPython(apply_unique_fields, migrations.RunPython.noop,)]
