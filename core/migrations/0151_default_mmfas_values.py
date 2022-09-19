from django.db import migrations, models

JAPAN_COUNTRY_CODE = "jp"  # core/datasets/countries.json


def apply_required_fields(apps, schema_editor):
    AgencyRegistrationRequest = apps.get_model('core', 'AgencyRegistrationRequest')
    Candidate = apps.get_model('core', 'Candidate')
    Agency = apps.get_model('core', 'Agency')
    User = apps.get_model('core', 'User')
    Job = apps.get_model('core', 'Job')

    Job.objects.update(country=JAPAN_COUNTRY_CODE)

    Agency.objects.update(country=JAPAN_COUNTRY_CODE)

    User.objects.filter(
        models.Q(agencyadministrator__isnull=False)
        | models.Q(agencymanager__isnull=False)
        | models.Q(recruiter__isnull=False)
    ).update(country=JAPAN_COUNTRY_CODE)

    # Update future agency users without agency profile
    User.objects.filter(
        pk__in=AgencyRegistrationRequest.objects.filter(
            created=False, user__country=''
        ).values_list('user__pk')
    ).update(country=JAPAN_COUNTRY_CODE)


class Migration(migrations.Migration):
    dependencies = [('core', '0150_prep_mmfas_required_fields')]

    operations = [
        migrations.RunPython(apply_required_fields, migrations.RunPython.noop)
    ]
