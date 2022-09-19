import React from 'react';

import PropTypes from 'prop-types';
import moment from 'moment';
import { Trans, plural } from '@lingui/macro';

import { Typography } from '@components';
import { getFormattedDate } from '@utils';

import styles from '../../JobPageContent.module.scss';

function JobOpenSince({ job }) {
  const { closedAt, updatedAt, status } = job;

  const today = moment(new Date());
  const publishedAt = moment(job.publishedAt);

  if (['filled', 'closed'].includes(status)) {
    return (
      <Typography className={styles.textLight}>
        <Trans>(since {getFormattedDate(closedAt || updatedAt)})</Trans>
      </Typography>
    );
  }

  const isOpenedToday = publishedAt.isSame(today, 'day');
  if (isOpenedToday) {
    return (
      <Typography className={styles.textLight}>
        <Trans>(Open Today)</Trans>
      </Typography>
    );
  }

  const isInFuture = publishedAt.diff(today) > 0;
  if (isInFuture) return null;

  const yearsOpen = today.diff(publishedAt, 'year');
  publishedAt.add(yearsOpen, 'years');

  const monthsOpen = today.diff(publishedAt, 'months');
  publishedAt.add(monthsOpen, 'months');

  const daysOpen = today.diff(publishedAt, 'days');

  if (!yearsOpen && !monthsOpen && !daysOpen) return null;

  const timeOpenParts = [];

  if (yearsOpen > 0)
    timeOpenParts.push(plural(yearsOpen, { one: '# year', other: '# years' }));

  if (monthsOpen > 0)
    timeOpenParts.push(plural(monthsOpen, { one: '# month', other: '# months' }));

  if (daysOpen > 0)
    timeOpenParts.push(plural(daysOpen, { one: '# day', other: '# days' }));

  const timeOpen = timeOpenParts.join(' ');

  return (
    <Typography className={styles.textLight}>
      <Trans>({timeOpen} open)</Trans>
    </Typography>
  );
}

JobOpenSince.propTypes = {
  job: PropTypes.shape({
    publishedAt: PropTypes.string,
    closedAt: PropTypes.string,
    updatedAt: PropTypes.string,
  }).isRequired,
};

export default JobOpenSince;
