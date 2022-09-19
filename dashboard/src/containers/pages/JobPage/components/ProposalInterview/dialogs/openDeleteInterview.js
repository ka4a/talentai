import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import { Button } from '@components';

export default function openDeleteInterview() {
  return openDialog({
    title: t`Delete Interview`,
    description: t`Are you sure you want to delete this Interview?`,
    getButtons: (resolve, reject) => (
      <>
        <Button onClick={resolve} variant='secondary' color='danger'>
          <Trans>Delete Interview</Trans>
        </Button>

        <Button onClick={reject} variant='secondary' color='neutral'>
          <Trans>Cancel</Trans>
        </Button>
      </>
    ),
  });
}
