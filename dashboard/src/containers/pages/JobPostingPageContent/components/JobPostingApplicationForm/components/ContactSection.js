import React from 'react';
import { useSelector } from 'react-redux';

import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { Typography } from '@components';

import styles from './Sections.module.scss';

const ContactSection = ({ FormInput }) => {
  const userCountry = useSelector((state) => state.user.country);

  return (
    <>
      <Typography variant='subheading'>
        <Trans>Contact</Trans>
      </Typography>

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.twoElements])}
      >
        <FormInput name='email' label={t`Email`} required />
        <FormInput
          name='phone'
          type='phone'
          label={t`Phone`}
          defaultCountry={userCountry}
        />
      </div>

      <hr />
    </>
  );
};

ContactSection.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default ContactSection;
