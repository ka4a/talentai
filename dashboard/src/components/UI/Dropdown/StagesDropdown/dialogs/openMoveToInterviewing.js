import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import { Button } from '@components';

export default function openMoveToInterviewing() {
  return openDialog({
    title: t`Move to Interviewing?`,
    description: t`Once in Interviewing, you will not be allowed to change the Application stage until all interviews are completed.`,
    getButtons: (resolve, reject) => (
      <>
        <Button onClick={reject} variant='secondary' color='neutral'>
          <Trans>Cancel</Trans>
        </Button>

        <Button onClick={resolve}>
          <Trans>Confirm</Trans>
        </Button>
      </>
    ),
  });
}
