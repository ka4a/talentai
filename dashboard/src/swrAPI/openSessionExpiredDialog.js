import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils/alert';
import Button from '@components/UI/Button';
import { makeSingletonPromiseCreator } from '@utils/common';

const openSessionExpiredDialog = makeSingletonPromiseCreator(() =>
  openDialog({
    title: t`Session Expired`,
    description: t`Your session has timed out. Please sign in again.`,
    getButtons: (resolve) => (
      <Button onClick={resolve}>
        <Trans>Sign In</Trans>
      </Button>
    ),
  })
);

export default openSessionExpiredDialog;
