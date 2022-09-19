import React from 'react';

import { Plural, t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import { Button } from '@components';

export default function openConfirmCloseUnfilled(availableOpenings) {
  return openDialog({
    title: t`Confirm closing with unfilled openings`,
    description: (
      <Trans>
        <Plural
          value={availableOpenings}
          one='There is still an opening available. Do you still want to close the job?'
          other='There are still # openings available. Do you still want to close the job?'
        />
      </Trans>
    ),
    getButtons: (resolve, reject) => (
      <>
        <Button onClick={resolve} variant='secondary' color='danger'>
          <Trans>Save anyway</Trans>
        </Button>

        <Button onClick={reject} variant='secondary' color='neutral'>
          <Trans>Keep editing</Trans>
        </Button>
      </>
    ),
  });
}
