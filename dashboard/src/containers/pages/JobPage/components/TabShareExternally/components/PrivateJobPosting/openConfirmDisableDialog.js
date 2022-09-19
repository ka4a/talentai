import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import Button from '@components/UI/Button';

const openConfirmDisableDialog = () =>
  openDialog({
    title: t`Disable Private Posting`,
    description: (
      <Trans>
        <p>Are you sure you want to disable your Private Posting?</p>
        <p>
          If you have shared that Private Posting with anyone outside your organization,
          that link will no longer be accessible
        </p>
        <div>If you re-enable your Private Posting, it will have a different URL</div>
      </Trans>
    ),
    getButtons: (resolve, reject) => (
      <>
        <Button onClick={resolve} variant='secondary' color='danger'>
          <Trans>Confirm Disable</Trans>
        </Button>

        <Button onClick={reject} variant='secondary'>
          <Trans>Cancel</Trans>
        </Button>
      </>
    ),
  });

export default openConfirmDisableDialog;
