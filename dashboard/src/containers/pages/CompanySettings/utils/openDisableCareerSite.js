import React from 'react';

import { t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';

import getCareerSiteDialogButtons from './getCareerSiteDialogButtons';

export default function openDisableCareerSite() {
  const title = t`Disable Career Site`;
  return openDialog({
    title,
    content: (
      <>
        <Trans>
          By disabling your Career Site, the Career Site URL will no longer be
          accessible.
        </Trans>

        <br />
        <br />

        <Trans>
          All the jobs you have published on your company Career Site will be
          unpublished.
        </Trans>
      </>
    ),
    getButtons: (resolve, reject) =>
      getCareerSiteDialogButtons(resolve, reject, {
        text: title,
        variant: 'secondary',
      }),
  });
}
