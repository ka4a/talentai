import React, { memo } from 'react';

import { t, Trans } from '@lingui/macro';
import PropTypes from 'prop-types';

import { LabeledItem, RatingInfo, Typography } from '@components';

import styles from '../ProposalInterview.module.scss';

const Assessments = ({ data }) => {
  if (!data) return null;

  return (
    <>
      <hr />

      <div className={styles.assessments}>
        <Typography variant='subheading'>
          <Trans>Assessment</Trans>
        </Typography>

        <LabeledItem
          className={styles.decision}
          label={t`Decision`}
          value={data.decisionDisplay}
        />

        <div className={styles.ratings}>
          {data.hiringCriteriaAssessment?.map((el) => (
            <RatingInfo key={el.id} label={el.name} rating={el.rating} />
          ))}
        </div>

        <LabeledItem
          label={t`Assessment Notes`}
          value={data.notes}
          variant='textarea'
        />
      </div>
    </>
  );
};

Assessments.propTypes = {
  data: PropTypes.shape({
    notes: PropTypes.string,
    decisionDisplay: PropTypes.string,
    hiringCriteriaAssessment: PropTypes.array,
  }),
};

Assessments.defaultProps = {
  data: null,
};

export default memo(Assessments);
