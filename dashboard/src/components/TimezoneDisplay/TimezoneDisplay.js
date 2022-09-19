import React, { memo } from 'react';

import moment from 'moment-timezone';
import { Trans } from '@lingui/macro';

import { getTimezoneOffset } from '@utils';
import { Typography } from '@components';
import { ReactComponent as Clock } from '@images/icons/clockOutlined.svg';

import styles from './TimezoneDisplay.module.scss';

const TimezoneDisplay = () => {
  const timezoneName = moment.tz.guess();

  return (
    <Typography variant='caption' className={styles.root}>
      <Clock className={styles.clock} />

      <Trans>
        The time zone is set to {timezoneName} (GMT{getTimezoneOffset()})
      </Trans>
    </Typography>
  );
};

export default memo(TimezoneDisplay);
