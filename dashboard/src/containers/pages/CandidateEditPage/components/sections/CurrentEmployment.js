import React from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t, Trans } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { FormSection, Typography } from '@components';
import {
  EMPLOYMENT_CHOICES,
  SALARY_CURRENCY_CHOICES,
  TAX_EQUALIZATION_CHOICES,
} from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from '../CandidateForm/CandidateForm.module.scss';

const CurrentEmployment = ({ FormInput }) => {
  const { i18n } = useLingui();
  const salaryCurrencyChoices = useTranslatedChoices(
    i18n,
    SALARY_CURRENCY_CHOICES,
    'description'
  );
  const employmentChoices = useTranslatedChoices(i18n, EMPLOYMENT_CHOICES);
  const taxEqualizationChoices = useTranslatedChoices(i18n, TAX_EQUALIZATION_CHOICES);

  return (
    <FormSection id='current-employment-edit' title={t`Current Employment`}>
      <div className={classnames([styles.rowWrapper, styles.twoElements])}>
        <FormInput name='currentPosition' label={t`Current Job Title`} />
        <FormInput name='currentCompany' label={t`Current Company`} />
      </div>

      <hr />

      <Typography variant='subheading'>
        <Trans>Compensation</Trans>
      </Typography>

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.threeElements])}
      >
        <FormInput
          type='select'
          name='currentSalaryCurrency'
          label={t`Currency`}
          options={salaryCurrencyChoices}
          labelKey='description'
          isDisabled // disabled due to ZOO-1036
        />
        <FormInput
          type='formatted-number'
          name='currentSalary'
          label={t`Current Annual Fixed`}
        />
        <FormInput
          type='formatted-number'
          name='currentSalaryVariable'
          label={t`Current Annual Variable`}
        />
      </div>

      <div className={styles.topGap}>
        <FormInput name='currentSalaryBreakdown' label={t`Compensation Notes`} />
      </div>

      <hr />

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.twoElements])}
      >
        <FormInput
          type='select'
          name='employmentStatus'
          label={t`Employment Type`}
          options={employmentChoices}
          clearable
        />
        <FormInput
          type='select'
          name='taxEqualization'
          label={t`Tax Equalization`}
          options={taxEqualizationChoices}
          clearable
        />
      </div>
    </FormSection>
  );
};

CurrentEmployment.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default CurrentEmployment;
