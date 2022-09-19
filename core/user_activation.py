from django.db import transaction

from core.models import User, Agency, Contract, Job, Client


def make_user_agency_admin(user, agency_id, job_id=None):
    agency = Agency.objects.get(id=agency_id)
    if agency is None:
        raise ValueError('Agency does not exist')

    agency.assign_recruiter(user)

    if job_id:
        job = Job.objects.get(id=job_id)
        if job and isinstance(job.organization, Client):
            # TODO: should the contract be initiated?
            Contract.objects.update_or_create(agency=agency, client=job.organization)

            job.assign_agency(agency)


USER_ACTIVATION_FUNCTIONS = {'make_user_agency_admin': make_user_agency_admin}


def activate_user(user):
    with transaction.atomic():
        if user.on_activation_action:
            fn = USER_ACTIVATION_FUNCTIONS.get(user.on_activation_action)

            if not fn:
                raise ValueError(
                    'User\'s activation action is not valid: {!r}'.format(
                        user.on_activation_action
                    )
                )

            activation_params = user.on_activation_params or {}
            fn(user, **activation_params)

        activated = User.objects.filter(id=user.id, is_activated=False).update(
            is_activated=True
        )

        if not activated:
            raise ValueError('User is already activated')

        user.refresh_from_db()


def get_agency_admin_activation_data(agency, job=None):
    action = 'make_user_agency_admin'
    assert action in USER_ACTIVATION_FUNCTIONS

    return {
        'on_activation_action': action,
        'on_activation_params': {
            'agency_id': agency.id,
            'job_id': job.id if job else None,
        },
    }
