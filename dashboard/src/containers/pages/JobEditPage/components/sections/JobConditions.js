import React from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { useLingui } from '@lingui/react';
import { t } from '@lingui/macro';

import { FormSection } from '@components';
import {
  JOB_FLEXTIME_ELIGIBILITY_CHOICES,
  JOB_TELEWORK_ELIGIBILITY_CHOICES,
  OTHER_BENEFITS_CHOICES,
  SALARY_CURRENCY_CHOICES,
  SALARY_PER_CHOICES,
  SOCIAL_INSURANCES_CHOICES,
} from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from '../JobForm/JobForm.module.scss';

const JobConditions = ({ FormInput }) => {
  const { i18n } = useLingui();

  const jobFlextimeEligibilityChoices = useTranslatedChoices(
    i18n,
    JOB_FLEXTIME_ELIGIBILITY_CHOICES
  );
  const jobTeleworkEligibilityChoices = useTranslatedChoices(
    i18n,
    JOB_TELEWORK_ELIGIBILITY_CHOICES
  );
  const otherBenefitsChoices = useTranslatedChoices(i18n, OTHER_BENEFITS_CHOICES);
  const salaryCurrencyChoices = useTranslatedChoices(
    i18n,
    SALARY_CURRENCY_CHOICES,
    'description'
  );
  const salaryPerChoices = useTranslatedChoices(i18n, SALARY_PER_CHOICES);
  const socialInsurancesChoices = useTranslatedChoices(i18n, SOCIAL_INSURANCES_CHOICES);

  return (
    <FormSection id='job-conditions-edit' title={t`Job Conditions`}>
      <div className={classnames([styles.rowWrapper, styles.salary])}>
        <FormInput
          type='select'
          name='salaryCurrency'
          label={i18n._(t`Currency`)}
          options={salaryCurrencyChoices}
          labelKey='description'
          isDisabled // disabled due to ZOO-1036
        />
        <FormInput
          type='formatted-number'
          name='salaryFrom'
          label={i18n._(t`Salary - Minimum`)}
          placeholder={i18n._(t`e.g. 500,000`)}
        />
        <FormInput
          type='formatted-number'
          name='salaryTo'
          label={i18n._(t`Salary - Maximum`)}
          placeholder={i18n._(t`e.g. 500,000`)}
        />
        <FormInput
          type='select'
          name='salaryPer'
          label={i18n._(t`Per`)}
          options={salaryPerChoices}
        />
      </div>

      <FormInput name='bonusSystem' label={i18n._(t`Bonus System`)} />

      <hr />

      <div className={classnames([styles.rowWrapper, styles.oneToTwoWrapper])}>
        <FormInput
          name='probationPeriodMonths'
          label={i18n._(t`Probation Period (months)`)}
        />
        <FormInput
          name='workLocation'
          label={i18n._(t`Work Location`)}
          placeholder={i18n._(t`e.g. New York`)}
        />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.twoElements, styles.topGap])}
      >
        <FormInput name='workingHours' label={i18n._(t`Working Hours`)} />
        <FormInput name='breakTimeMins' label={i18n._(t`Break Time (min)`)} />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.twoElements, styles.topGap])}
      >
        <FormInput
          type='select'
          name='flexitimeEligibility'
          label={i18n._(t`Flextime Eligibility`)}
          options={jobFlextimeEligibilityChoices}
          clearable
        />
        <FormInput
          type='select'
          name='teleworkEligibility'
          label={i18n._(t`Telework Eligibility`)}
          options={jobTeleworkEligibilityChoices}
          clearable
        />
      </div>

      <div className={styles.topGap}>
        <FormInput name='overtimeConditions' label={i18n._(t`Overtime Conditions`)} />
      </div>

      <div
        className={classnames([
          styles.rowWrapper,
          styles.oneToTwoWrapper,
          styles.topGap,
        ])}
      >
        <FormInput name='paidLeaves' label={i18n._(t`Paid Leave Days (Annual)`)} />
        <FormInput name='additionalLeaves' label={i18n._(t`Additional Leave`)} />
      </div>

      <hr />

      <div className={styles.topGap}>
        <FormInput
          type='multi-select'
          name='socialInsurances'
          label={i18n._(t`Social Insurance`)}
          options={socialInsurancesChoices}
        />
      </div>

      <div className={styles.topGap}>
        <FormInput
          name='commutationAllowance'
          label={i18n._(t`Commutation Allowance`)}
        />
      </div>

      <div className={styles.topGap}>
        <FormInput
          type='multi-select'
          name='otherBenefits'
          label={i18n._(t`Other Benefits`)}
          options={otherBenefitsChoices}
        />
      </div>
    </FormSection>
  );
};

JobConditions.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default JobConditions;
