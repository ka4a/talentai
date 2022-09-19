import React, { useMemo, memo } from 'react';

import { t } from '@lingui/macro';

import { getFormattedDate } from '@utils';
import { Badge, LabeledItem, Typography } from '@components';

import styles from '../../CandidateDetailsSection.module.scss';

const Interview = (props) => {
  const {
    title,
    company,
    startAt,
    endAt,
    currentlyPursuing,
    description,
    location,
  } = props;

  const endDate = useMemo(() => {
    if (currentlyPursuing) return t`Current`;
    return getFormattedDate(endAt);
  }, [currentlyPursuing, endAt]);

  return (
    <div className={styles.detailsItem}>
      <div className={styles.header}>
        <div className={styles.title}>
          <Typography>{title}</Typography>
        </div>

        <div className={styles.control}>
          <Badge variant={'neutral'} text={company} />
        </div>
      </div>

      <div className={styles.details}>
        <div className={styles.multiRowWrapper}>
          <LabeledItem label={t`Start date`} value={getFormattedDate(startAt)} />
          <LabeledItem label={t`End Date`} value={endDate} />
          <LabeledItem label={t`Location`} value={location} />
        </div>

        <LabeledItem
          label={t`Responsibilities`}
          value={description}
          variant='textarea'
        />
      </div>
    </div>
  );
};

export default memo(Interview);
