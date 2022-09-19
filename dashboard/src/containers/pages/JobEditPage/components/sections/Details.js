import React from 'react';

import classnames from 'classnames';
import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { FormSection } from '@components';
import { useFunctionList } from '@swrAPI';
import { JOB_EMPLOYMENT_TYPE_CHOICES, REASON_FOR_OPENING_CHOICES } from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from '../JobForm/JobForm.module.scss';

const Details = ({ FormInput }) => {
  const functions = useFunctionList();
  const { i18n } = useLingui();
  const jobEmploymentTypeChoices = useTranslatedChoices(
    i18n,
    JOB_EMPLOYMENT_TYPE_CHOICES
  );
  const reasonForOpeningChoices = useTranslatedChoices(
    i18n,
    REASON_FOR_OPENING_CHOICES
  );

  return (
    <FormSection id='details-edit' title={t`Details`}>
      <FormInput name='title' label={t`Job Title`} tabIndex='1' required />

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.twoElements])}
      >
        <FormInput
          type='select'
          name='function'
          label={t`Function`}
          options={functions}
          isSearchable
          clearable
        />
        <FormInput
          type='select'
          name='employmentType'
          label={t`Employment Type`}
          options={jobEmploymentTypeChoices}
          clearable
        />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.threeElements])}
      >
        <FormInput name='department' label={t`Department`} tabIndex='2' />
        <FormInput
          type='select'
          name='reasonForOpening'
          label={t`Reason for Opening`}
          options={reasonForOpeningChoices}
          clearable
        />
        <FormInput
          type='simple-datepicker'
          name='targetHiringDate'
          label={t`Target Hiring Date`}
          format='YYYY-MM-DD'
          tabIndex='3'
        />
      </div>

      <FormInput
        type='rich-editor'
        wrapperClassName={styles.topGap}
        name='mission'
        label={t`Mission`}
      />

      <FormInput
        type='rich-editor'
        wrapperClassName={styles.topGap}
        name='responsibilities'
        label={t`Responsibilities`}
        required
      />
    </FormSection>
  );
};

Details.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default Details;
