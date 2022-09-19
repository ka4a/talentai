import React, { memo, useMemo } from 'react';

import groupBy from 'lodash/groupBy';
import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { INTERVIEW_ITEMS_CHOICES } from '@constants';
import { JobStatusesAccordion, Typography } from '@components';
import { useTranslatedChoices } from '@hooks';

import StageList from '../StageList';

import styles from './InterviewingStage.module.scss';

const InterviewingStage = ({ data }) => {
  const { i18n } = useLingui();
  const interviewItemsChoices = useTranslatedChoices(i18n, INTERVIEW_ITEMS_CHOICES);

  const subStages = useMemo(() => {
    const groupedData = groupBy(data, 'subStage');
    return interviewItemsChoices.map((el) => ({
      title: el.name,
      count: groupedData[el.value]?.length ?? 0,
      data: groupedData[el.value] ?? [],
    }));
  }, [data, interviewItemsChoices]);

  return (
    <JobStatusesAccordion
      title={t`Interviewing`}
      count={data.length}
      disabled={!data.length}
      isOpen={data.length > 0}
      content={
        <div className={styles.wrapper}>
          {subStages.map((subStage) => (
            <div key={subStage.title} className={styles.subStage}>
              <Typography
                variant='bodyStrong'
                className={classnames([
                  styles.sectionTitle,
                  { [styles.disabled]: !subStage.count },
                ])}
              >
                {subStage.title} ({subStage.count})
              </Typography>

              {subStage.data.length > 0 && <StageList data={subStage.data} />}
            </div>
          ))}
        </div>
      }
    />
  );
};

InterviewingStage.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
};

export default memo(InterviewingStage);
