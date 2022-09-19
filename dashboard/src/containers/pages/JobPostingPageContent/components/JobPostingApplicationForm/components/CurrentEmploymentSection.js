import React from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t, Trans } from '@lingui/macro';

import { Typography } from '@components';

import styles from './Sections.module.scss';

const CurrentEmploymentSection = ({ FormInput }) => (
  <>
    <Typography variant='subheading'>
      <Trans>Current Employment</Trans>
    </Typography>

    <div className={classnames([styles.rowWrapper, styles.topGap, styles.twoElements])}>
      <FormInput name='currentPosition' label={t`Current Job Title`} />
      <FormInput name='currentCompany' label={t`Current Company`} />
    </div>

    <hr />
  </>
);

CurrentEmploymentSection.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default CurrentEmploymentSection;
