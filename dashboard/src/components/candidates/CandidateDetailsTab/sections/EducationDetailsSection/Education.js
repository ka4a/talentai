import React, { useMemo, memo } from 'react';

import moment from 'moment';
import { t } from '@lingui/macro';

import { Badge, LabeledItem, Typography } from '@components';

import styles from '../../CandidateDetailsSection.module.scss';

const Education = (props) => {
  const { title, company, endAt, currentlyPursuing, department } = props;

  const dateAndTime = useMemo(() => {
    if (currentlyPursuing) return t`Current`;
    return endAt ? moment(endAt).format('YYYY') : '';
  }, [currentlyPursuing, endAt]);

  return (
    <div className={styles.detailsItem}>
      <div className={styles.header}>
        <div className={styles.title}>
          <Typography>{title}</Typography>
        </div>

        <div className={styles.control}>
          <Badge className={styles.badge} variant={'neutral'} text={company} />
        </div>
      </div>

      <div className={styles.details}>
        <div className={styles.multiRowWrapper}>
          <LabeledItem label={t`Field of Study`} value={department} />
          <LabeledItem label={t`Year Completed (or Expected)`} value={dateAndTime} />
        </div>
      </div>
    </div>
  );
};

export default memo(Education);
