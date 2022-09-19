import React from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t, Trans } from '@lingui/macro';

import { FormSection, Typography } from '@components';

import styles from '../CandidateForm/CandidateForm.module.scss';

const Contact = ({ FormInput }) => {
  const countriesOptions = useSelector((state) => state.settings.localeData.countries);
  const userCountry = useSelector((state) => state.user.country);

  return (
    <FormSection id='contact-edit' title={t`Contact`}>
      <div className={classnames([styles.rowWrapper, styles.twoElements])}>
        <FormInput name='email' label={t`Email (Primary)`} />
        <FormInput name='secondaryEmail' label={t`Email (Secondary)`} />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.twoElements])}
      >
        <FormInput
          name='phone'
          label={t`Phone Number (Primary)`}
          type='phone'
          defaultCountry={userCountry}
        />
        <FormInput
          name='secondaryPhone'
          label={t`Phone Number (Secondary)`}
          type='phone'
          defaultCountry={userCountry}
        />
      </div>

      <hr />

      <Typography variant='subheading'>
        <Trans>Address</Trans>
      </Typography>

      <div
        className={classnames([
          styles.rowWrapper,
          styles.topGap,
          styles.addressWrapper,
        ])}
      >
        <FormInput name='currentStreet' label={t`Street`} />
        <FormInput name='currentCity' label={t`City`} />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.threeElements])}
      >
        <FormInput name='currentPrefecture' label={t`Prefecture`} />
        <FormInput name='currentPostalCode' label={t`Postal Code`} />
        <FormInput
          type='select'
          name='currentCountry'
          label={t`Country`}
          options={countriesOptions}
          valueKey='code'
          searchable
          clearable
        />
      </div>

      <hr />

      <Typography variant='subheading'>
        <Trans>Online Profiles</Trans>
      </Typography>

      <div className={styles.topGap}>
        <FormInput name='linkedinUrl' label={t`Linkedin`} />
      </div>
    </FormSection>
  );
};

Contact.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default Contact;
