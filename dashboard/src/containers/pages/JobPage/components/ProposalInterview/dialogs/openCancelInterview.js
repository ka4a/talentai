import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import { Button } from '@components';

import CancelInterviewModal from '../components/CancelInterviewModal';

export default function openCancelInterview(proposal) {
  return openDialog({
    title: t`Cancel Interview`,
    content: <CancelInterviewModal proposal={proposal} />,
    getButtons: (resolve, reject) => (
      <>
        <Button onClick={resolve} variant='secondary' color='danger'>
          <Trans>Cancel Interview</Trans>
        </Button>

        <Button onClick={reject} variant='secondary' color='neutral'>
          <Trans>Cancel</Trans>
        </Button>
      </>
    ),
  });
}
