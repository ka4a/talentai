import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import { Button, Typography } from '@components';

export default function openResetJobPostingDialog() {
  return openDialog({
    title: t`Reset Content`,
    description: (
      <Trans>
        <Typography className='mb-3'>
          Are you sure you want to reset your job posting content?
        </Typography>
        <Typography className='text-danger'>
          This will reset any fields you may have edited on your job posting to the job
          details value
        </Typography>
      </Trans>
    ),
    getButtons,
  });
}

const getButtons = (resolve, reject) => (
  <>
    <Button onClick={reject} variant='secondary'>
      <Trans>Cancel</Trans>
    </Button>
    <Button onClick={resolve}>
      <Trans>Reset Content</Trans>
    </Button>
  </>
);
