import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import Button from '@components/UI/Button';

export default function openDeleteFile() {
  return openDialog({
    title: t`Delete File`,
    description: t`Are you sure you want to delete this file?`,
    getButtons: (resolve, reject) => (
      <>
        <Button onClick={resolve} variant='secondary' color='danger'>
          <Trans>Delete File</Trans>
        </Button>

        <Button onClick={reject} variant='secondary' color='neutral'>
          <Trans>Cancel</Trans>
        </Button>
      </>
    ),
  });
}
