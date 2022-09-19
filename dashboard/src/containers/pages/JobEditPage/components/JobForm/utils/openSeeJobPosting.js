import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import { Button } from '@components';

export default function openSeeJobPosting() {
  return openDialog({
    title: t`Update Job Postings`,
    description: (
      <Trans>
        This job is currently shared externally. If you have changed the Job content,
        you may want to update your job postings.
      </Trans>
    ),
    getButtons: (resolve, reject) => (
      <>
        <Button variant='secondary' onClick={resolve}>
          <Trans>Review Postings</Trans>
        </Button>
        <Button onClick={reject}>
          <Trans>Done</Trans>
        </Button>
      </>
    ),
  });
}
