import React from 'react';

import { useLingui } from '@lingui/react';
import { t } from '@lingui/macro';

import BlockKPI from './BlockKPI';

export default function OpenJobsKPI(props) {
  const { i18n } = useLingui();

  return (
    <BlockKPI title={i18n._(t`Open Jobs`)} operationId='stats_open_jobs' {...props} />
  );
}
