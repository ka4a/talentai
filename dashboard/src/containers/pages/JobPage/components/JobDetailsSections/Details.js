import React, { memo } from 'react';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';

import { LabeledItem, FormSection } from '@components';

import styles from './JobDetailsSections.module.scss';

const Details = ({ job, privatePart }) => {
  return (
    <FormSection id='job-details' titleVariant='subheading' title={t`Details`}>
      {privatePart}

      <LabeledItem label={t`Mission`} variant='textarea' value={job.mission} />

      <hr />

      <LabeledItem
        className={styles.topGap}
        label={t`Responsibilities`}
        variant='textarea'
        value={job.responsibilities}
      />
    </FormSection>
  );
};

Details.propTypes = {
  job: PropTypes.shape({
    title: PropTypes.string,
    mission: PropTypes.string,
    responsibilities: PropTypes.string,
    employmentType: PropTypes.string,
    department: PropTypes.string,
    reasonForOpening: PropTypes.string,
    targetHiringData: PropTypes.string,
    function: PropTypes.shape({
      id: PropTypes.number,
      title: PropTypes.string,
    }),
  }).isRequired,
  privatePart: PropTypes.node,
};

Details.defaultProps = {
  privatePart: null,
};

export default memo(Details);
