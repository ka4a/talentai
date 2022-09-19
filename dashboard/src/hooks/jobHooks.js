import { useSelector } from 'react-redux';
import { useRouteMatch } from 'react-router-dom';

import { useGetJob } from '@swrAPI';
import { useIsAuthenticatedByRoles } from '@hooks';
import { CLIENT_ADMINISTRATORS, CLIENT_INTERNAL_RECRUITERS } from '@constants';

export const useIsAllowedToOpenJobForm = () => {
  const { data: job = {} } = useGetJob();
  const { createdBy, recruiters } = job;

  const isAddJobForm = useRouteMatch('/c/jobs/add');

  const userId = useSelector((state) => state.user?.id);

  const isAdministrator = useIsAuthenticatedByRoles([CLIENT_ADMINISTRATORS]);
  const isInternalRecruiter = useIsAuthenticatedByRoles([CLIENT_INTERNAL_RECRUITERS]);

  const isRelatedToJob =
    createdBy?.id === userId || recruiters?.find((el) => el.id === userId);

  return isAdministrator || (isInternalRecruiter && (isAddJobForm || isRelatedToJob));
};
