import React, { useEffect } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { FormSection } from '@components';
import {
  JOB_CHANGE_URGENCY_CHOICES,
  NOTICE_PERIOD_CHOICES,
  OTHER_DESIRED_BENEFIT_CHOICES,
  SALARY_CURRENCY_CHOICES,
} from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from '../CandidateForm/CandidateForm.module.scss';

const CandidateExpectations = (props) => {
  const { otherDesiredBenefits, FormInput, setValue } = props;

  const { i18n } = useLingui();
  const jobChangeUrgencyChoices = useTranslatedChoices(
    i18n,
    JOB_CHANGE_URGENCY_CHOICES
  );
  const noticePeriodChoices = useTranslatedChoices(i18n, NOTICE_PERIOD_CHOICES);
  const otherDesiredBenefitChoices = useTranslatedChoices(
    i18n,
    OTHER_DESIRED_BENEFIT_CHOICES
  );
  const salaryCurrencyChoices = useTranslatedChoices(
    i18n,
    SALARY_CURRENCY_CHOICES,
    'description'
  );

  useEffect(() => {
    const isIncludeOtherOption = otherDesiredBenefits.includes('other');

    if (!isIncludeOtherOption) setValue('otherDesiredBenefitsOthersDetail', '');
  }, [otherDesiredBenefits, setValue]);

  return (
    <FormSection id='candidate-expectations-edit' title={t`Candidate Expectations`}>
      <div className={classnames([styles.rowWrapper, styles.threeElements])}>
        <FormInput
          type='select'
          name='salaryCurrency'
          label={t`Currency`}
          options={salaryCurrencyChoices}
          labelKey='description'
          isDisabled // disabled due to ZOO-1036
        />
        <FormInput type='formatted-number' name='salary' label={t`Desired Salary`} />
        <FormInput
          name='potentialLocations'
          label={t`Desired Location(s)`}
          withoutCapitalize
        />
      </div>

      <div className={classnames([styles.rowWrapper, styles.topGap])}>
        <FormInput
          type='multi-select'
          name='otherDesiredBenefits'
          label={t`Other Desired Benefits`}
          options={otherDesiredBenefitChoices}
        />
      </div>

      {otherDesiredBenefits.includes('other') && (
        <div className={classnames([styles.halfWidth, styles.topGap])}>
          <FormInput name='otherDesiredBenefitsOthersDetail' label={t`Other`} />
        </div>
      )}

      <FormInput
        type='rich-editor'
        wrapperClassName={styles.topGap}
        name='expectationsDetails'
        label={t`Expectations Details`}
      />

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.twoElements])}
      >
        <FormInput
          type='select'
          name='jobChangeUrgency'
          label={t`Job Change Urgency`}
          options={jobChangeUrgencyChoices}
          clearable
        />
        <FormInput
          type='select'
          name='noticePeriod'
          label={t`Notice Period`}
          options={noticePeriodChoices}
          clearable
        />
      </div>
    </FormSection>
  );
};

CandidateExpectations.propTypes = {
  otherDesiredBenefits: PropTypes.arrayOf(PropTypes.string).isRequired,
  FormInput: PropTypes.func.isRequired,
  setValue: PropTypes.func.isRequired,
};

export default CandidateExpectations;
