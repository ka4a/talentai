import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import { Button } from '@components';

export default function openSkipInterview() {
  return openDialog({
    title: t`Skip Interview`,
    description: (
      <>
        <Trans>
          Are you sure you want to skip this interview?
          <br />
          This action cannot be undone.
        </Trans>
      </>
    ),
    getButtons: (resolve, reject) => (
      <>
        <Button onClick={resolve} variant='secondary' color='danger'>
          <Trans>Skip Interview</Trans>
        </Button>

        <Button onClick={reject} variant='secondary' color='neutral'>
          <Trans>Cancel</Trans>
        </Button>
      </>
    ),
  });
}
