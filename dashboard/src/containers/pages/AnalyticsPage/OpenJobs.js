import React from 'react';

import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import ChartBlock from './ChartBlock';

function OpenJobs(props) {
  const { filterType, filterValue, filterValueName, i18n } = props;

  let helpText = [i18n._(t`Max number of open jobs`)];

  if (filterType === 'team') {
    helpText.push(filterValue === null ? '' : i18n._(t`for department`));
  } else if (filterType === 'hiring_manager') {
    helpText.push(filterValue === null ? '' : i18n._(t`for hiring manager`));
  } else if (filterType === 'function') {
    helpText.push(filterValue === null ? '' : i18n._(t`for function`));
  }

  if (filterValue !== null) {
    helpText.push(`"${filterValueName}"`);
  }

  helpText = helpText.join(' ');

  return (
    <ChartBlock
      operationId='stats_open_jobs'
      title={i18n._(t`Open Jobs`)}
      helpText={helpText}
      {...props}
    />
  );
}

export default withI18n()(OpenJobs);
