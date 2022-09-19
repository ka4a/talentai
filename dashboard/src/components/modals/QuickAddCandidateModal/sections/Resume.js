import React, { memo } from 'react';

import { Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { ResumeInput, Typography } from '@components';

import styles from '../QuickAddCandidateModal.module.scss';

const Resume = ({ form, setValue }) => (
  <>
    <Typography
      variant='subheading'
      className={classnames([styles.subtitle, styles.topGap])}
    >
      <Trans>Resume</Trans>
    </Typography>

    <ResumeInput {...{ form, setValue }} />
  </>
);

Resume.propTypes = {
  form: PropTypes.shape({}).isRequired,
  setValue: PropTypes.func.isRequired,
};

export default memo(Resume);
