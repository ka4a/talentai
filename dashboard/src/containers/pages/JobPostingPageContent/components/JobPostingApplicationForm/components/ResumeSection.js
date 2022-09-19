import React, { memo } from 'react';

import { Trans } from '@lingui/macro';
import PropTypes from 'prop-types';

import { ResumeInput, Typography } from '@components';

import styles from './Sections.module.scss';

const ResumeSection = ({ form, setValue }) => (
  <>
    <Typography variant='subheading'>
      <Trans>Resume</Trans>
      <span className={styles.required}>*</span>
    </Typography>

    <div className={styles.topGap}>
      <ResumeInput form={form} setValue={setValue} />
    </div>
  </>
);

ResumeSection.propTypes = {
  form: PropTypes.shape({}).isRequired,
  setValue: PropTypes.func.isRequired,
};

export default memo(ResumeSection);
