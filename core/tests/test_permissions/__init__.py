from .admin import AdminTests

# TODO(ZOO-827): remove these
# from .agency_administrator import (
#     AgencyAdministratorTests,
#     TestProposalInterviewViewSet as AgencyAdministratorTestProposalInterviewViewSet,
# )
# from .agency_manager import (
#     AgencyManagerTests,
#     TestProposalInterviewViewSet as AgencyManagerTestProposalInterviewViewSet,
# )
from .anonymous import (
    AnonymousTests,
    TestProposalInterviewViewSet as AnonymousTestProposalInterviewViewSet,
)

# TODO(ZOO-827): remove these
# from .hiring_manager import (
#     HiringManagerTests,
#     TestProposalInterviewViewSet as HiringManagerTestProposalInterviewViewSet,
# )
# from .recruiter import (
#     RecruiterTests,
#     TestProposalInterviewViewSet as RecruiterTestProposalInterviewViewSet,
# )
# from .talent_associate import (
#     TalentAssociateTests,
#     TestProposalInterviewViewSet as TalentAssociateTestProposalInterviewViewSet,
# )

from .client_roles import ClientRolesTests
