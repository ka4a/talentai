import { t } from '@lingui/macro';

import { openDialog } from '@utils';

import getCareerSiteDialogButtons from './getCareerSiteDialogButtons';

export default function openEnableCareerSite() {
  const title = t`Enable Career Site`;
  return openDialog({
    title,
    content: t`By enabling your company Career Site, you will be able to publish Jobs visible to anyone.`,
    getButtons: (resolve, reject) =>
      getCareerSiteDialogButtons(resolve, reject, { text: title, variant: 'primary' }),
  });
}
