import React from 'react';

import classnames from 'classnames';
import _ from 'lodash';
import { useLingui } from '@lingui/react';

import { JOB_STATUS_CHOICES } from '@constants';

export default function JobStatus({ status }) {
  const { i18n } = useLingui();

  const obj = _.find(JOB_STATUS_CHOICES, { value: status });

  if (!obj) {
    console.error(`Job Status "${status}" is not defined`);
    return <span>{status}</span>;
  }

  return (
    <span className={classnames({ [`text-${obj.color}`]: obj.color })}>
      {i18n._(obj.name)}
    </span>
  );
}
