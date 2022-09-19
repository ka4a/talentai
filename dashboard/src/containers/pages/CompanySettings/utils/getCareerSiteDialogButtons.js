import React from 'react';

import { Trans } from '@lingui/macro';

import { Button } from '@components';

const getCareerSiteDialogButtons = (resolve, reject, confirmButtonProps) => (
  <>
    <Button onClick={reject} variant='secondary' color='neutral'>
      <Trans>Cancel</Trans>
    </Button>

    <Button onClick={resolve} variant={confirmButtonProps.variant} color='danger'>
      {confirmButtonProps.text}
    </Button>
  </>
);

export default getCareerSiteDialogButtons;
