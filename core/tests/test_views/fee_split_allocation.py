from djangorestframework_camel_case.util import camelize
from rest_framework.test import APITestCase
from core.tests.generic_response_assertions import GenericResponseAssertionSet
from django.core.files.uploadedfile import SimpleUploadedFile


from core import serializers as s, fixtures as f, models as m

DRAFT = m.FeeStatus.DRAFT.key
APPROVED = m.FeeStatus.APPROVED.key
PENDING = m.FeeStatus.PENDING.key


def get_default_data(fee):
    proposal = fee.placement.proposal
    agency = proposal.created_by.org
    lead_bd_consultant = f.create_agency_manager(agency)
    client_info = m.AgencyClientInfo.objects.filter(
        client=proposal.job.client, agency=agency,
    ).first()
    candidate = proposal.candidate

    return dict(
        fee=fee.id,
        client_originator=client_info.originator_id,
        candidate_owner=candidate.owner_id,
        activator=candidate.activator_id,
        lead_candidate_consultant=candidate.lead_consultant_id,
        lead_bd_consultant=lead_bd_consultant.id,
        support_consultant=candidate.support_consultant_id,
        candidate_source=candidate.source,
        **f.DEFAULT_ALLOCATION_SPLIT,
    )


class SplitAllocationTest(APITestCase):
    def create_user(self):
        raise NotImplementedError

    def create_other_user(self):
        return f.create_agency_administrator(self.agency)

    def create_proposal(self):
        user = f.create_recruiter(self.agency)

        job = f.create_job(org=self.client_obj, client=self.client_obj)
        job.assign_member(user)
        job.assign_agency(self.agency)

        candidate = f.create_candidate(
            self.agency,
            created_by=user,
            owner=f.create_agency_manager(self.agency,),
            activator=f.create_agency_manager(self.agency),
            lead_consultant=f.create_agency_manager(self.agency),
            support_consultant=f.create_agency_manager(self.agency),
            source='Job Boards',
        )

        return f.create_proposal(job, candidate, user)

    def setUp(self):
        self.assert_response = GenericResponseAssertionSet(self)

        self.client_obj = f.create_client()
        self.agency = f.create_agency()

        self.user = self.create_user()

        self.client.force_login(self.user)

        f.create_contract(self.agency, self.client_obj)

        m.AgencyClientInfo.objects.create(
            client=self.client_obj,
            agency=self.agency,
            originator=f.create_agency_manager(
                self.agency, email='client.originator@localhost'
            ),
            industry=m.Industry.ELECTRONIC_GOODS.key,
            type=m.ClientType.NEW_ACCOUNT.key,
        )

        self.proposal = self.create_proposal()

    def check(self, assertion, created_by, submitted_by=None, status=DRAFT):
        raise NotImplementedError

    def assert_unrelated(self, *args, **kwargs):
        raise NotImplementedError

    def assert_unrelated_pending(self, *args, **kwargs):
        raise NotImplementedError

    def assert_unrelated_approved(self, *args, **kwargs):
        raise NotImplementedError

    def assert_created(self, *args, **kwargs):
        raise NotImplementedError

    def assert_created_pending(self, *args, **kwargs):
        raise NotImplementedError

    def assert_created_approved(self, *args, **kwargs):
        raise NotImplementedError

    def assert_submitted(self, *args, **kwargs):
        raise NotImplementedError

    def assert_submitted_pending(self, *args, **kwargs):
        raise NotImplementedError

    def assert_submitted_approved(self, *args, **kwargs):
        raise NotImplementedError

    def test_unrelated(self):
        other_user = self.create_other_user()
        self.check(self.assert_unrelated, other_user)

    def test_unrelated_pending(self):
        other_user = self.create_other_user()
        self.check(self.assert_unrelated_pending, other_user, other_user, PENDING)

    def test_unrelated_approved(self):
        other_user = self.create_other_user()
        self.check(self.assert_unrelated_approved, other_user, other_user, APPROVED)

    def test_submitted(self):
        other_user = self.create_other_user()
        self.check(self.assert_submitted, other_user, self.user)

    def test_submitted_pending(self):
        other_user = self.create_other_user()
        self.check(self.assert_submitted_pending, other_user, self.user, PENDING)

    def test_submitted_approved(self):
        other_user = self.create_other_user()
        self.check(self.assert_submitted_approved, other_user, self.user, APPROVED)

    def test_created(self):
        self.check(self.assert_created, self.user)

    def test_created_pending(self):
        other_user = self.create_other_user()
        self.check(self.assert_created_pending, self.user, other_user, PENDING)

    def test_created_approved(self):
        other_user = self.create_other_user()
        self.check(self.assert_created_approved, self.user, other_user, APPROVED)


class RetrieveMixin:
    def check(self, assertion, created_by, submitted_by=None, status=DRAFT):
        allocation = f.create_split_allocation(
            self.agency, self.proposal, created_by, submitted_by, status
        )

        assertion('get', 'fee_split_allocation-detail', allocation.id)


class TalentAssociateSplitAllocation(SplitAllocationTest):
    def create_user(self):
        return f.create_client_administrator(self.client_obj)

    def assert_unrelated(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_unrelated_pending(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_created(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_created_pending(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_submitted(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_submitted_pending(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)


class HiringManagerSplitAllocation(TalentAssociateSplitAllocation):
    def create_user(self):
        return f.create_hiring_manager(self.client_obj)


class AgencyAdminSplitAllocation(SplitAllocationTest):
    def create_user(self):
        return f.create_agency_administrator(self.agency)

    def assert_unrelated(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_unrelated_pending(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_created(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_created_pending(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_submitted(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_submitted_pending(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)


class AgencyManagerSplitAllocation(AgencyAdminSplitAllocation):
    def create_user(self):
        return f.create_agency_manager(self.agency)


class RecruiterSplitAllocation(AgencyAdminSplitAllocation):
    def create_user(self):
        return f.create_recruiter(self.agency)

    def assert_unrelated(self, *args, **kwargs):
        self.assert_response.not_found(*args, **kwargs)

    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.not_found(*args, **kwargs)

    def assert_unrelated_pending(self, *args, **kwargs):
        self.assert_response.not_found(*args, **kwargs)


class TalentAssociateRetrieveSplitAllocation(
    RetrieveMixin, TalentAssociateSplitAllocation
):
    pass


class HiringManagerRetrieveSplitAllocation(RetrieveMixin, HiringManagerSplitAllocation):
    pass


class AgencyAdminRetrieveSplitAllocation(RetrieveMixin, AgencyAdminSplitAllocation):
    pass


class AgencyManagerRetrieveSplitAllocation(RetrieveMixin, AgencyManagerSplitAllocation):
    pass


class RecruiterRetrieveSplitAllocation(RetrieveMixin, RecruiterSplitAllocation):
    def assert_ok_not_editable(self, *args, **kwargs):
        response_data = self.assert_response.ok(*args, **kwargs).json()
        self.assertFalse(response_data['isEditable'])

    def assert_created_approved(self, *args, **kwargs):
        self.assert_ok_not_editable(*args, **kwargs)

    def assert_created_pending(self, *args, **kwargs):
        self.assert_ok_not_editable(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_ok_not_editable(*args, **kwargs)

    def assert_submitted_pending(self, *args, **kwargs):
        self.assert_ok_not_editable(*args, **kwargs)


class UpdateMixin:
    def check(self, assertion, created_by, submitted_by=None, status=DRAFT):
        allocation = f.create_split_allocation(
            self.agency, self.proposal, created_by, submitted_by, status
        )

        data = get_default_data(allocation.fee)

        assertion('patch', 'fee_split_allocation-detail', allocation.id, data)


class TalentAssociateUpdateSplitAllocation(UpdateMixin, TalentAssociateSplitAllocation):
    pass


class HiringManagerUpdateSplitAllocation(UpdateMixin, HiringManagerSplitAllocation):
    pass


class AgencyAdminUpdateSplitAllocation(UpdateMixin, AgencyAdminSplitAllocation):
    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)


class AgencyManagerUpdateSplitAllocation(UpdateMixin, AgencyManagerSplitAllocation):
    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)


class RecruiterUpdateSplitAllocation(UpdateMixin, RecruiterSplitAllocation):
    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_created_pending(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)

    def assert_submitted_pending(self, *args, **kwargs):
        self.assert_response.no_permission(*args, **kwargs)


class CreateMixin:
    def check(
        self, assertion, created_by, submitted_by=None, status=DRAFT, new_status=None
    ):
        fee = f.create_fee(
            proposal=self.create_proposal(),
            created_by=created_by,
            submitted_by=submitted_by,
            status=status,
            agency=self.agency,
        )

        data = get_default_data(fee)
        if new_status:
            data['fee_status'] = new_status

        return assertion('post', 'fee_split_allocation-list', data=data)


class CreateAgencyUserMixin:
    def assert_unrelated(self, *args, **kwargs):
        self.assert_response.created(*args, **kwargs)

    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_unrelated_pending(self, *args, **kwargs):
        self.assert_response.created(*args, **kwargs)

    def assert_created(self, *args, **kwargs):
        self.assert_response.created(*args, **kwargs)

    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_created_pending(self, *args, **kwargs):
        self.assert_response.created(*args, **kwargs)

    def assert_submitted(self, *args, **kwargs):
        self.assert_response.created(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_submitted_pending(self, *args, **kwargs):
        self.assert_response.created(*args, **kwargs)


class TalentAssociateCreateSplitAllocation(CreateMixin, TalentAssociateSplitAllocation):
    pass


class HiringManagerCreateSplitAllocation(CreateMixin, HiringManagerSplitAllocation):
    pass


class AgencyAdminCreateSplitAllocation(
    CreateMixin, CreateAgencyUserMixin, AgencyAdminSplitAllocation
):
    pass


class AgencyManagerCreateSplitAllocation(
    CreateMixin, CreateAgencyUserMixin, AgencyManagerSplitAllocation
):
    pass


class RecruiterCreateSplitAllocation(
    CreateMixin, CreateAgencyUserMixin, RecruiterSplitAllocation
):
    def assert_unrelated(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_unrelated_pending(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_created_pending(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def assert_submitted_pending(self, *args, **kwargs):
        self.assert_response.bad_request(*args, **kwargs)

    def test_returns_not_editable(self):
        response_data = self.check(
            self.assert_response.created, self.user, new_status=PENDING
        ).json()
        self.assertFalse(response_data['isEditable'])


class UploadFileMixin:
    def check(self, assertion, created_by, submitted_by=None, status=DRAFT):
        allocation = f.create_split_allocation(
            self.agency, self.proposal, created_by, submitted_by, status
        )

        data = {'file': SimpleUploadedFile('file.txt', b'')}

        assertion(
            'post',
            'fee_split_allocation-upload-file',
            allocation.pk,
            data,
            format='multipart',
        )


class AgencyAdminUploadFileSplitAllocation(
    UploadFileMixin, AgencyAdminUpdateSplitAllocation
):
    # TODO: 403 after upload-flow is fixed
    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)


class AgencyManagerUploadFileSplitAllocation(
    UploadFileMixin, AgencyManagerUpdateSplitAllocation
):
    # TODO: 403 after upload-flow is fixed
    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)


class RecruiterUploadFileSplitAllocation(
    UploadFileMixin, RecruiterUpdateSplitAllocation
):
    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_created_pending(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_submitted_pending(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)


class TalentAssociateUploadFileSplitAllocation(
    UploadFileMixin, TalentAssociateUpdateSplitAllocation
):
    pass


class HiringManagerUploadFileSplitAllocation(
    UploadFileMixin, HiringManagerUpdateSplitAllocation
):
    pass


class DeleteFileMixin:
    def check(self, assertion, created_by, submitted_by=None, status=DRAFT):
        allocation = f.create_split_allocation(
            self.agency, self.proposal, created_by, submitted_by, status
        )
        allocation.file = SimpleUploadedFile('file.txt', b'')
        allocation.save()

        assertion(
            'delete', 'fee_split_allocation-delete-file', allocation.pk,
        )


class AgencyAdminDeleteFileSplitAllocation(
    DeleteFileMixin, AgencyAdminUpdateSplitAllocation
):
    def test_file_deleted(self):
        allocation = f.create_split_allocation(
            self.agency, self.proposal, self.user, self.user
        )
        allocation.file = SimpleUploadedFile('file.txt', b'')
        self.assert_response.ok(
            'delete', 'fee_split_allocation-delete-file', allocation.pk,
        )

        allocation.refresh_from_db()

        assert_error = self.assertRaisesMessage(
            ValueError, "The 'file' attribute has no file associated with it."
        )
        with assert_error:
            allocation.file.file

    # TODO: 403 after upload-flow is fixed
    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)


class AgencyManagerDeleteFileSplitAllocation(
    DeleteFileMixin, AgencyManagerUpdateSplitAllocation
):
    # TODO: 403 after upload-flow is fixed
    def assert_unrelated_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_submitted_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)

    def assert_created_approved(self, *args, **kwargs):
        self.assert_response.ok(*args, **kwargs)


class RecruiterDeleteFileSplitAllocation(
    DeleteFileMixin, RecruiterUpdateSplitAllocation
):
    pass


class TalentAssociateDeleteFileSplitAllocation(
    DeleteFileMixin, TalentAssociateUpdateSplitAllocation
):
    pass


class HiringManagerDeleteFileSplitAllocation(
    DeleteFileMixin, HiringManagerUpdateSplitAllocation
):
    pass


class GetFileMixin:
    def check(self, assertion, created_by, submitted_by=None, status=DRAFT):
        allocation = f.create_split_allocation(
            self.agency, self.proposal, created_by, submitted_by, status
        )
        allocation.file = SimpleUploadedFile('file.txt', b'')
        allocation.save()

        assertion(
            'get', 'fee_split_allocation-get-file', allocation.pk,
        )


class AgencyAdminGetFileSplitAllocation(
    GetFileMixin, AgencyAdminRetrieveSplitAllocation
):
    pass


class AgencyManagerGetFileSplitAllocation(
    GetFileMixin, AgencyManagerRetrieveSplitAllocation
):
    pass


class RecruiterGetFileSplitAllocation(GetFileMixin, RecruiterSplitAllocation):
    pass


class TalentAssociateGetFileSplitAllocation(
    GetFileMixin, TalentAssociateRetrieveSplitAllocation
):
    pass


class HiringManagerGetFileSplitAllocation(
    GetFileMixin, HiringManagerRetrieveSplitAllocation
):
    pass
