import random
import secrets
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core import models as m

FLOWS = [
    ['new'],
    ['new', 'approved'],
    ['new', 'rejected'],
    ['new', 'approved', 'interviewing'],
    ['new', 'approved', 'interviewing', 'proceeding'],
    ['new', 'approved', 'interviewing', 'proceeding', 'offer'],
    ['new', 'approved', 'interviewing', 'proceeding', 'offer', 'offer_accepted'],
    ['new', 'approved', 'interviewing', 'proceeding', 'offer', 'offer_declined'],
]


class Command(BaseCommand):
    help = 'Generate some analytics data'

    def add_arguments(self, parser):
        parser.add_argument('client_id', nargs=1, type=int)

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            self._handle(*args, **kwargs)

    def _handle(self, *args, **options):
        client = m.Client.objects.get(pk=options['client_id'][0])

        runid = secrets.token_hex(4)

        functions = m.Function.objects.order_by('?')[:4]

        candidates = []

        for i in range(100):
            candidates.append(
                m.Candidate.objects.create(
                    organization=client,
                    first_name='Dummy',
                    last_name='Candidate{}{}'.format(runid, i),
                    email='dummy_{}_{}@localhost'.format(runid, i),
                    summary='123',
                    source=random.choice(m.CandidateSources.choices),
                )
            )

        managers = list(m.User.objects.filter(hiringmanager__client=client))

        for i in range(100):
            published_at = timezone.now() - timedelta(days=random.randint(2, 365))
            closed_at = min(
                timezone.now(), published_at + timedelta(days=random.randint(2, 60))
            )

            job = m.Job.objects.create(
                client=client,
                function=random.choice(functions),
                title='ClosedJob{}'.format(secrets.token_hex(4)),
                responsibilities='dummy closed job',
                published=True,
                status=m.JobStatus.CLOSED.key,
                published_at=published_at,
                closed_at=closed_at,
            )

            job.assign_manager(random.choice(managers))

            ignore_offer_accepted = False  # one hire per job

            for candidate in random.sample(candidates, 8):
                proposal_created_at = published_at + (
                    (closed_at - published_at) * (random.random() / 3)
                )

                proposal = m.Proposal.objects.create(
                    job=job,
                    candidate=candidate,
                    created_by=random.choice(managers),
                    created_at=proposal_created_at,
                )

                flow = random.choice(FLOWS)
                last_date_used = proposal_created_at

                status = None

                for f in flow:
                    if f == 'offer_accepted':
                        if ignore_offer_accepted:
                            break
                        else:
                            ignore_offer_accepted = True

                    last_date_used = last_date_used + (
                        (closed_at - last_date_used) * (random.random() / 3)
                    )

                    status = m.ProposalStatus.objects.filter(group=f).first()

                    psh = m.ProposalStatusHistory.objects.create(
                        proposal=proposal, status=status, changed_at=last_date_used
                    )
                    psh.changed_at = last_date_used
                    psh.save()

                proposal.status = status
                proposal.updated_at = last_date_used
                proposal.save()
