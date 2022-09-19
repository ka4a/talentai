import React from 'react';

import { t, Trans } from '@lingui/macro';

import Button from '@components/UI/Button';
import { openDialog } from '@utils/alert';

const getConfirmArchivingButtons = (resolve, reject) => (
  <>
    <Button onClick={resolve} variant='secondary' color='danger'>
      <Trans>Archive</Trans>
    </Button>

    <Button onClick={reject} variant='secondary' color='neutral'>
      <Trans>Cancel</Trans>
    </Button>
  </>
);

const confirmArchivingCandidate = () => {
  return openDialog({
    title: t`Confirm archiving`,
    description: t`This candidate will be archived. You will be able to restore it in the future.`,
    getButtons: getConfirmArchivingButtons,
  });
};

export default confirmArchivingCandidate;
