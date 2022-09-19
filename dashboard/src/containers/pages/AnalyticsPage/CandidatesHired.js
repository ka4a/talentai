import React from 'react';

import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import ChartBlock from './ChartBlock';

function CandidatesHired(props) {
  const { filterType, filterValue, filterValueName, i18n } = props;

  let helpText = [i18n._(t`Hired Candidates`)];

  if (filterType === 'team') {
    helpText.push(filterValue === null ? '' : i18n._(t`by department`));
  } else if (filterType === 'hiring_manager') {
    helpText.push(filterValue === null ? '' : i18n._(t`by hiring manager`));
  } else if (filterType === 'function') {
    helpText.push(filterValue === null ? '' : i18n._(t`in function`));
  }

  if (filterValue !== null) {
    helpText.push(`"${filterValueName}"`);
  }

  helpText = helpText.join(' ');

  return (
    <ChartBlock
      operationId='stats_candidates_hired'
      title={i18n._(t`Candidates Hired`)}
      helpText={helpText}
      {...props}
    />
  );
}

export default withI18n()(CandidatesHired);
