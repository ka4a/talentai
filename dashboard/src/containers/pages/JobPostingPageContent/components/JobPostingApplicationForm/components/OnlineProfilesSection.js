import React from 'react';

import PropTypes from 'prop-types';
import { t, Trans } from '@lingui/macro';

import { Typography } from '@components';

import styles from './Sections.module.scss';

const OnlineProfilesSection = ({ FormInput }) => (
  <>
    <Typography variant='subheading'>
      <Trans>Online Profiles</Trans>
    </Typography>

    <div className={styles.topGap}>
      <FormInput name='linkedinUrl' label={t`Linkedin`} />
    </div>

    <hr />
  </>
);

OnlineProfilesSection.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default OnlineProfilesSection;
