import factory

from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify

from core import models as m


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.User
        django_get_or_create = ('email',)

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    country = 'jp'
    password = 'testpassword'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        key_fields = dict(email=kwargs.get('email'))
        user = model_class.objects.filter(**key_fields).first()
        if user:
            return user
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)


class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.Client
        django_get_or_create = ('name',)

    class Params:
        unique = False
        career_site = factory.Trait(
            is_career_site_enabled=True,
            career_site_slug=factory.LazyAttribute(lambda o: slugify(o.name)),
        )

    name = factory.LazyAttributeSequence(
        lambda o, n: 'Company %d' % (n) if o.unique else 'Client A'
    )
    primary_contact = factory.SubFactory(UserFactory)


class AgencyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.Agency


class ClientAdministratorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.ClientAdministrator
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory)


class ClientInternalRecruiterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.ClientInternalRecruiter
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory)


class ClientStandardUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.ClientStandardUser
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory)


class AbstractOrgFactory(factory.django.DjangoModelFactory):
    org_id = factory.SelfAttribute('organization.id')
    org_content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.organization)
    )

    class Meta:
        exclude = ['organization']
        abstract = True


class JobQuestionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.JobQuestion

    text = factory.Faker('bs')


class JobFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.JobFile

    title = factory.Sequence(lambda n: f'Attachment {n}')
    file = factory.django.FileField(filename='job_attachment.pdf')


class HiringCriterionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.HiringCriterion

    name = factory.Sequence(lambda n: f'Hiring Criteria {n}')


class ClientJobFactory(AbstractOrgFactory):
    class Meta:
        model = m.Job

    class Params:
        client_admin = factory.SubFactory(ClientAdministratorFactory)

    owner = factory.SelfAttribute('client_admin.user')
    client = factory.SubFactory(ClientFactory)
    organization = factory.LazyAttribute(lambda o: o.client)
    title = factory.Faker('job')
    country = 'jp'
    work_location = factory.Faker('city', locale='ja_JP')
    mission = factory.Faker('bs')
    responsibilities = factory.Faker('paragraph', nb_sentences=7)
    requirements = factory.Faker('paragraph', nb_sentences=7)
    questions = factory.RelatedFactoryList(
        JobQuestionFactory, factory_related_name='job', size=3
    )
    jobfile_set = factory.RelatedFactoryList(
        JobFileFactory, factory_related_name='job', size=1
    )
    hiring_criteria = factory.RelatedFactoryList(
        HiringCriterionFactory, factory_related_name='job', size=3
    )
    salary_from = factory.Faker(
        'pyint', min_value=1000000, max_value=50000000, step=1000
    )
    salary_to = factory.LazyAttribute(lambda o: o.salary_from + 2000000)

    @factory.post_generation
    def interview_templates(obj, create, extracted, **kwargs):
        if not create:
            return
        obj.create_default_interview_templates()
        return obj.interview_templates.all()


class PrivateJobPostingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.PrivateJobPosting

    job = factory.SubFactory(ClientJobFactory)


class CareerSiteJobPostingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.CareerSiteJobPosting

    job = factory.SubFactory(ClientJobFactory)


class ClientCandidateFactory(AbstractOrgFactory):
    class Meta:
        model = m.Candidate

    class Params:
        client_recruiter = factory.SubFactory(
            ClientInternalRecruiterFactory, client=factory.SelfAttribute('..client')
        )
        client = factory.SubFactory(ClientFactory)

    owner = factory.SelfAttribute('client_recruiter.user')
    organization = factory.LazyAttribute(lambda o: o.owner.profile.client)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')


class ClientProposalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.Proposal

    class Params:
        client = factory.SubFactory(ClientFactory)

    job = factory.SubFactory(ClientJobFactory, client=factory.SelfAttribute('..client'))
    candidate = factory.SubFactory(
        ClientCandidateFactory, client=factory.SelfAttribute('..client')
    )
    status = factory.LazyFunction(
        lambda: m.ProposalStatus.objects.filter(
            group=m.ProposalStatusGroup.ASSOCIATED_TO_JOB
        ).first()
    )
    created_by = factory.LazyAttribute(lambda o: o.candidate.owner)

    @factory.post_generation
    def default_interviews(obj, create, extracted, **kwargs):
        if not create:
            return
        obj.create_default_interviews()
        return obj.interviews.all()

    @factory.post_generation
    def default_questions(obj, create, extracted, **kwargs):
        if not create:
            return
        obj.create_default_questions()
        return obj.questions.all()


class HiringCriterionAssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.HiringCriterionAssessment

    hiring_criterion = factory.SubFactory(HiringCriterionFactory)
    rating = factory.Iterator([1, 2, 3, 4, 5])


class ProposalInterviewAssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.ProposalInterviewAssessment

    hiring_criterion_assessment = factory.RelatedFactory(
        HiringCriterionAssessmentFactory,
        factory_related_name='assessment',
        hiring_criterion__job=factory.SelfAttribute(
            '..assessment.interview.proposal.job'
        ),
    )
    decision = factory.Iterator(
        m.ProposalInterviewAssessment.DECISION_CHOICES, getter=lambda c: c[0]
    )
    notes = factory.Faker('bs')


class NoteActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.NoteActivity

    content = factory.Faker('paragraph', nb_sentences=3)


class ProposalInterviewFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = m.ProposalInterview

    class Params:
        client = None

    proposal = factory.SubFactory(
        ClientProposalFactory, client=factory.SelfAttribute('..client')
    )
    created_by = factory.SelfAttribute('proposal.created_by')
