import React from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { FormSection } from '@components';
import { GENDERS_CHOICES, NATIONALITIES_CHOICES } from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from '../CandidateForm/CandidateForm.module.scss';

const twoElementsStyles = classnames([
  styles.rowWrapper,
  styles.topGap,
  styles.twoElements,
]);

const Personal = ({ FormInput }) => {
  const { i18n } = useLingui();
  const genderChoices = useTranslatedChoices(i18n, GENDERS_CHOICES);
  const nationalitiesChoices = useTranslatedChoices(i18n, NATIONALITIES_CHOICES);

  return (
    <FormSection id='personal-edit' title={t`Personal`}>
      <div className={classnames([styles.rowWrapper, styles.threeElements])}>
        <FormInput name='firstName' label={t`First Name`} required />
        <FormInput name='middleName' label={t`Middle Name`} />
        <FormInput name='lastName' label={t`Last Name(s)`} withoutCapitalize required />
      </div>

      <div className={twoElementsStyles}>
        <FormInput name='firstNameKanji' label={t`First Name (Kanji)`} />
        <FormInput name='lastNameKanji' label={t`Last Name (Kanji)`} />
      </div>

      <div className={twoElementsStyles}>
        <FormInput name='firstNameKatakana' label={t`First Name (Katakana)`} />
        <FormInput name='lastNameKatakana' label={t`Last Name (Katakana)`} />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.threeElements])}
      >
        <FormInput
          type='simple-datepicker'
          name='birthdate'
          label={t`Date of Birth`}
          format='YYYY-MM-DD'
        />
        <FormInput
          type='select'
          name='nationality'
          label={t`Nationality`}
          options={nationalitiesChoices}
          searchable
        />
        <FormInput
          type='select'
          name='gender'
          label={t`Gender`}
          options={genderChoices}
          clearable
        />
      </div>
    </FormSection>
  );
};

Personal.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default Personal;
