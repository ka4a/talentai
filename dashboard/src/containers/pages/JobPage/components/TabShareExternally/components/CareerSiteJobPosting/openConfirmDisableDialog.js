import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import Button from '@components/UI/Button';

const openConfirmDisableDialog = () =>
  openDialog({
    title: t`Unpublish Job Posting`,
    description: (
      <Trans>
        <p>Are you sure you want to unpublish your job from your company Career Site</p>
        <div>Your job will no longer be listed on your Career Site</div>
      </Trans>
    ),
    getButtons: (resolve, reject) => (
      <>
        <Button onClick={resolve} variant='secondary' color='danger'>
          <Trans>Confirm Unpublish</Trans>
        </Button>

        <Button onClick={reject} variant='secondary'>
          <Trans>Cancel</Trans>
        </Button>
      </>
    ),
  });

export default openConfirmDisableDialog;
