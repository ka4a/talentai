from django.db.models import Q, Value, BooleanField, Max, Case, When

from core.models import Candidate

boolean_field = BooleanField()


def flag(condition):
    return Case(
        When(condition, then=Value(True, boolean_field)),
        default=Value(False, boolean_field),
    )


def get_possible_condition(new_candidate):
    cond_is_possible = Q(
        first_name=new_candidate['first_name'], last_name=new_candidate['last_name']
    )

    first_name_kanji = new_candidate.get('first_name_kanji', None)
    last_name_kanji = new_candidate.get('last_name_kanji', None)

    if first_name_kanji and last_name_kanji:
        cond_is_possible = cond_is_possible | Q(
            first_name_kanji=first_name_kanji, last_name_kanji=last_name_kanji,
        )

    id = new_candidate.get('id', None)
    if id:
        cond_is_possible = cond_is_possible & ~Q(id=id)

    return cond_is_possible


def email_match(field, new_candidate, data_field):
    return Q(**{field: new_candidate.get(data_field, '')})


def one_of_emails(field, new_candidate):
    return (
        email_match(field, new_candidate, 'email')
        | email_match(field, new_candidate, 'secondary_email')
    ) & ~Q(**{f'{field}__exact': ''})


def get_absolute_condition(new_candidate):
    cond_is_absolute = one_of_emails('email', new_candidate) | one_of_emails(
        'secondary_email', new_candidate
    )

    linkedin_url = new_candidate.get('linkedin_url', '')
    if linkedin_url != '':
        cond_is_absolute = cond_is_absolute | Q(linkedin_url=linkedin_url)

    zoho_id = new_candidate.get('zoho_id', '')
    if zoho_id != '':
        cond_is_absolute = cond_is_absolute | Q(zoho_id=zoho_id)

    id = new_candidate.get('id', None)
    if id:
        cond_is_absolute = cond_is_absolute & ~Q(id=id) & Q(original__isnull=True)

    return cond_is_absolute


def check_candidate_duplication(new_candidate, profile):
    cond_is_absolute = get_absolute_condition(new_candidate)
    cond_is_possible = get_possible_condition(new_candidate)

    queryset = Candidate.objects.filter(cond_is_absolute | cond_is_possible)

    qs_on_job = Candidate.objects.filter(
        proposals__job=new_candidate.get('job'), proposals__job_id__isnull=False
    )

    qs_owned = profile.apply_own_candidates_filter(queryset)

    qs_not_owned = qs_on_job.exclude(id__in=qs_owned.values('id'))

    submitted_by_others = None
    if qs_not_owned.filter(cond_is_absolute).exists():
        submitted_by_others = 'ABSOLUTE'
    elif qs_not_owned.filter(cond_is_possible).exists():
        submitted_by_others = 'POSSIBLE'

    qs_on_job_owned = profile.apply_own_candidates_filter(qs_on_job)

    qs_on_job_same_group = qs_on_job_owned.filter(cond_is_absolute)

    qs_owned_include_archived = profile.apply_own_candidates_filter(
        Candidate.archived_objects.filter(cond_is_absolute & Q(archived=True))
    )

    if not qs_on_job_same_group.exists():
        qs_on_job_same_group = qs_on_job_owned.filter(cond_is_possible)

    return {
        'queryset': qs_owned.annotate(
            is_absolute=flag(cond_is_absolute),
            is_submitted=flag(Q(id__in=qs_on_job.values('id'))),
        ),
        'submitted_by_others': submitted_by_others,
        'last_submitted': qs_on_job_same_group.aggregate(
            Max('proposals__created_at')
        ).get('proposals__created_at__max'),
        'to_restore': qs_owned_include_archived,
    }
