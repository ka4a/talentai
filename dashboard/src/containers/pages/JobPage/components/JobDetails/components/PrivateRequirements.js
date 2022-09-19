import React from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';

import { LabeledItem } from '@components';
import { getChoiceName } from '@utils';
import styles from '@styles/form.module.scss';

function PrivateRequirements({ job }) {
  const workExperienceOptions = useSelector(
    (state) => state.settings.localeData.workExperiences
  );

  return (
    <div className={classnames(styles.rowWrapper, styles.twoElements, styles.topGap)}>
      <LabeledItem label={t`Education Level`} value={job.educationalLevel} />
      <LabeledItem
        label={t`Work Experience`}
        value={getChoiceName(workExperienceOptions, job.workExperience, 'label')}
      />
    </div>
  );
}

PrivateRequirements.propTypes = {
  job: PropTypes.object.isRequired,
};

export default PrivateRequirements;
