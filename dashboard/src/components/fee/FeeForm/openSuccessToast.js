import { toast } from 'react-toastify';
import React from 'react';

import { Trans } from '@lingui/macro';

const TOAST_OPTIONS = {
  type: 'success',
  position: 'bottom-center',
  autoClose: 5000,
  className: 'toast-alert',
  closeOnClick: true,
};

const showToast = (content) => toast.success(content, TOAST_OPTIONS);

const openSuccessToast = (proposal, status) => {
  const formName = proposal ? (
    <Trans>
      {proposal.job.clientName} - {proposal.candidate.name}&apos;s placement form{' '}
    </Trans>
  ) : (
    <Trans>Fee form</Trans>
  );

  switch (status) {
    case 'pending':
      showToast(<Trans>{formName} has been successfully submitted</Trans>);
      break;
    case 'approved':
      showToast(<Trans>{formName} has been successfully saved and approved</Trans>);
      break;
    case 'needs_revision':
      showToast(
        <Trans>{formName} has been successfully saved and sent to revision</Trans>
      );
      break;
    default:
      showToast(<Trans>{formName} has been successfully saved</Trans>);
      break;
  }
};

export default openSuccessToast;
