import React, { memo } from 'react';

import { useLingui } from '@lingui/react';
import { t } from '@lingui/macro';

import BlockKPI from './BlockKPI';

function CandidatesHiredKPI(props) {
  const { i18n } = useLingui();

  return (
    <BlockKPI
      title={i18n._(t`Candidates Hired`)}
      operationId='stats_candidates_hired'
      {...props}
    />
  );
}

export default memo(CandidatesHiredKPI);
