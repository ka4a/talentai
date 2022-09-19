import React from 'react';

import { t, Trans } from '@lingui/macro';

import Button from '@components/UI/Button';
import { openDialog } from '@utils/alert';

const getConfirmDeleteCandidateButtons = (resolve, reject) => (
  <>
    <Button onClick={resolve} variant='secondary' color='danger'>
      <Trans>Delete</Trans>
    </Button>

    <Button onClick={reject} variant='secondary' color='neutral'>
      <Trans>Cancel</Trans>
    </Button>
  </>
);

const confirmDeletionCandidate = () => {
  return openDialog({
    title: t`Confirm deletion`,
    description: t`Once deleted, you will not be able to restore the candidate.`,
    getButtons: getConfirmDeleteCandidateButtons,
  });
};

export default confirmDeletionCandidate;
