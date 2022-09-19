from django.db import migrations, models
from django.db.models import Q, Count


def annotate_job_hired_count(queryset):
    return queryset.annotate(
        hired_count=Count(
            'proposals__id',
            filter=Q(
                proposals__status__group='offer_accepted', proposals__stage='shortlist',
            ),
            distinct=True,
        ),
    )


def add_openigns(apps, schema_editor):
    Job = apps.get_model('core', 'Job')
    for job in annotate_job_hired_count(Job.objects.all()):
        hired_count = job.hired_count

        if job.openings_count <= hired_count:
            openings_count = hired_count + 1 if job.status != 'filled' else hired_count

            if job.openings_count != openings_count:
                job.openings_count = openings_count
                job.save()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0129_zoho_linkedin_unique_together'),
    ]

    operations = [migrations.RunPython(add_openigns, migrations.RunPython.noop)]
