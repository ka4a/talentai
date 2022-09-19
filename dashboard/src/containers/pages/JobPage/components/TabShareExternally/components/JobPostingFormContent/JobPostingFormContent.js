import React from 'react';

import { t } from '@lingui/macro';
import classNames from 'classnames';

import {
  FormContextDynamicList,
  FormContextField,
  FormContextLanguageField,
  FormContextTagsField,
  FormContextTranslatedSelect,
  FormSection,
} from '@components';
import {
  JOB_EMPLOYMENT_TYPE_CHOICES,
  JOB_FLEXTIME_ELIGIBILITY_CHOICES,
  JOB_TELEWORK_ELIGIBILITY_CHOICES,
  OTHER_BENEFITS_CHOICES,
  SALARY_CURRENCY_CHOICES,
  SALARY_PER_CHOICES,
  SOCIAL_INSURANCES_CHOICES,
} from '@constants';
import formStyles from '@styles/form.module.scss';
import { useFunctionList } from '@swrAPI';

import styles from './JobPostingFormContent.module.scss';

function JobPostingFormContent(props) {
  const functions = useFunctionList();

  const classNameSets = {
    twoFields: classNames(
      formStyles.rowWrapper,
      formStyles.topGap,
      formStyles.twoElements
    ),
    threeFields: classNames(
      formStyles.rowWrapper,
      formStyles.topGap,
      formStyles.threeElements
    ),
    twoFields1to2: classNames(
      formStyles.rowWrapper,
      formStyles.topGap,
      formStyles.oneToTwoWrapper
    ),
    manyFields: classNames(
      formStyles.rowWrapper,
      formStyles.withGaps,
      formStyles.topGap
    ),
  };

  return (
    <>
      <FormSection id='details-edit' title={t`Details`}>
        <FormContextField tabIndex='1' required label={t`Job Title`} name='title' />
        <div className={classNameSets.twoFields}>
          <FormContextField
            type='select'
            name='function'
            label={t`Function`}
            options={functions}
            isSearchable
            clearable
          />
          <FormContextTranslatedSelect
            options={JOB_EMPLOYMENT_TYPE_CHOICES}
            name='employmentType'
            label={t`Employment Type`}
            clearable
          />
        </div>

        <FormContextField
          label={t`Mission`}
          type='rich-editor'
          wrapperClassName={formStyles.topGap}
          name='mission'
        />

        <FormContextField
          label={t`Responsibilities`}
          type='rich-editor'
          wrapperClassName={formStyles.topGap}
          name='responsibilities'
          required
        />
      </FormSection>

      <FormSection
        id='job-requirements'
        titleVariant='subheading'
        title={t`Requirements`}
      >
        <FormContextField
          label={t`Requirements`}
          type='rich-editor'
          wrapperClassName={formStyles.topGap}
          name='requirements'
          required
        />

        <hr />

        <FormContextTagsField
          label={t`Skills`}
          name='skills'
          tagType='skill'
          className={formStyles.topGap}
        />

        <hr />

        <FormContextLanguageField name='requiredLanguages' />
      </FormSection>

      <FormSection id='job-conditions-edit' title={t`Job Conditions`}>
        <div className={classNameSets.manyFields}>
          <FormContextTranslatedSelect
            name='salaryCurrency'
            label={t`Currency`}
            options={SALARY_CURRENCY_CHOICES}
            labelKey='description'
            isDisabled // disabled due to ZOO-1036
          />

          <FormContextField
            type='formatted-number'
            name='salaryFrom'
            label={t`Salary - Minimum`}
            placeholder={t`e.g. 500,000`}
          />

          <FormContextField
            type='formatted-number'
            name='salaryTo'
            label={t`Salary - Maximum`}
            placeholder={t`e.g. 500,000`}
          />

          <FormContextTranslatedSelect
            fieldWrapperClassName={styles.salaryPer}
            name='salaryPer'
            label={t`Per`}
            options={SALARY_PER_CHOICES}
          />
        </div>

        <div className={formStyles.topGap}>
          <FormContextField name='bonusSystem' label={t`Bonus System`} />
        </div>

        <hr />

        <div className={classNameSets.twoFields1to2}>
          <FormContextField
            name='probationPeriodMonths'
            label={t`Probation Period (months)`}
          />
          <FormContextField
            name='workLocation'
            label={t`Work Location`}
            placeholder={t`e.g. New York`}
          />
        </div>

        <div className={classNameSets.twoFields}>
          <FormContextField name='workingHours' label={t`Working Hours`} />
          <FormContextField name='breakTimeMins' label={t`Break Time (min)`} />
        </div>
        <div className={classNameSets.twoFields}>
          <FormContextTranslatedSelect
            name='flexitimeEligibility'
            label={t`Flextime Eligibility`}
            options={JOB_FLEXTIME_ELIGIBILITY_CHOICES}
            clearable
          />
          <FormContextTranslatedSelect
            name='teleworkEligibility'
            label={t`Telework Eligibility`}
            options={JOB_TELEWORK_ELIGIBILITY_CHOICES}
            clearable
          />
        </div>

        <div className={formStyles.topGap}>
          <FormContextField name='overtimeConditions' label={t`Overtime Conditions`} />
        </div>

        <div className={classNameSets.twoFields1to2}>
          <FormContextField name='paidLeaves' label={t`Paid Leave Days (Annual)`} />
          <FormContextField name='additionalLeaves' label={t`Additional Leave`} />
        </div>

        <hr />

        <div className={formStyles.topGap}>
          <FormContextTranslatedSelect
            type='multi-select'
            name='socialInsurances'
            label={t`Social Insurance`}
            options={SOCIAL_INSURANCES_CHOICES}
          />
        </div>

        <div className={formStyles.topGap}>
          <FormContextField
            name='commutationAllowance'
            label={t`Commutation Allowance`}
          />
        </div>

        <div className={formStyles.topGap}>
          <FormContextTranslatedSelect
            type='multi-select'
            name='otherBenefits'
            label={t`Other Benefits`}
            options={OTHER_BENEFITS_CHOICES}
          />
        </div>
      </FormSection>

      <FormSection title={t`Screening questions`}>
        <FormContextDynamicList
          addRowText={t`+ Add Screening Question`}
          name='questions'
          rowTemplate={SCREENING_QUESTION_TEMPLATE}
        />
      </FormSection>
    </>
  );
}

const SCREENING_QUESTION_TEMPLATE = { text: '' };

JobPostingFormContent.propTypes = {};

export default JobPostingFormContent;
