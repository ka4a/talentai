from django.db import migrations, models
from django.db.models import Q, Value, BooleanField, Case, When

boolean_field = BooleanField()


def flag(condition):
    return Case(
        When(condition, then=Value(True, boolean_field)),
        default=Value(False, boolean_field)
    )


def get_possible_condition(new_candidate):
    cond_is_possible = Q(
        first_name=new_candidate['first_name'],
        last_name=new_candidate['last_name']
    )

    first_name_ja = new_candidate.get('first_name_ja', None)
    last_name_ja = new_candidate.get('last_name_ja', None)

    if first_name_ja and last_name_ja:
        cond_is_possible = cond_is_possible | Q(
            first_name_ja=new_candidate['first_name_ja'],
            last_name_ja=new_candidate['last_name_ja']
        )

    id = new_candidate.get('id', None)
    if id:
        cond_is_possible = cond_is_possible & ~Q(id=id)

    return cond_is_possible & Q(original__isnull=True)



def email_match(field, new_candidate, data_field):
    return Q(**{field: new_candidate.get(data_field, '')})


def one_of_emails(field, new_candidate):
    return (
        (
            email_match(field, new_candidate, 'email')
            | email_match(field, new_candidate, 'secondary_email')
        )
        & ~Q(**{f'{field}__exact': ''})
    )


def get_absolute_condition(new_candidate):
    cond_is_absolute = (
        one_of_emails('email', new_candidate)
        | one_of_emails('secondary_email', new_candidate)
    )

    linkedin_url = new_candidate.get('linkedin_url', '')
    if linkedin_url != '':
        cond_is_absolute = cond_is_absolute | Q(linkedin_url=linkedin_url)

    id = new_candidate.get('id', None)
    if id:
        cond_is_absolute = cond_is_absolute & ~Q(id=id)

    return cond_is_absolute & Q(original__isnull=True)


def link_to_candidate_original(apps, schema_editor):
    """Add Job File Permissions."""

    Candidate = apps.get_model('core', 'Candidate')

    for candidate in Candidate.objects.all().order_by('-created_at'):
        data = {
            'id': candidate.id,
            'email': candidate.email,
            'secondary_email': candidate.secondary_email,
            'linkedin_url': candidate.linkedin_url,
            'first_name': candidate.first_name,
            'last_name': candidate.last_name,
            'first_name_ja': candidate.first_name_ja,
            'last_name_ja': candidate.last_name_ja,
        }
        duplicates = Candidate.objects\
            .filter(
                get_absolute_condition(data)
                | get_possible_condition(data),
                org_id=candidate.org_id,
                org_content_type=candidate.org_content_type,
            )\
            .order_by('created_at')[:1]\
            .values_list('id', flat=True)

        candidate.original_id = duplicates[0] if len(duplicates) > 0 else None
        candidate.save()
        


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0124_candidate_original'),
    ]

    operations = [
        migrations.RunPython(
            link_to_candidate_original, migrations.RunPython.noop
        )
    ]
