import React, { memo } from 'react';

import classnames from 'classnames';
import { t, Trans } from '@lingui/macro';
import { useLingui } from '@lingui/react';
import PropTypes from 'prop-types';

import { FormattedSalary, LabeledItem, Typography, FormSection } from '@components';
import { getChoiceName } from '@utils';
import {
  JOB_FLEXTIME_ELIGIBILITY_CHOICES,
  JOB_TELEWORK_ELIGIBILITY_CHOICES,
  OTHER_BENEFITS_CHOICES,
  SOCIAL_INSURANCES_CHOICES,
} from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from './JobDetailsSections.module.scss';

const JobConditions = ({ job }) => {
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
  const socialInsurancesChoices = useTranslatedChoices(i18n, SOCIAL_INSURANCES_CHOICES);

  const getSeparatedString = (choices, value = []) =>
    value.map((socialInsurance) => getChoiceName(choices, socialInsurance)).join(', ');

  return (
    <FormSection
      id='job-conditions'
      titleVariant='subheading'
      title={t`Job Conditions`}
    >
      <div className={classnames([styles.rowWrapper, styles.twoElements])}>
        <div>
          <Typography variant='caption' className={styles.label}>
            <Trans>Annual Salary</Trans>
          </Typography>

          <Typography>
            <FormattedSalary job={job} isAnnual hidePerName />
          </Typography>
        </div>

        <div>
          <Typography variant='caption' className={styles.label}>
            <Trans>Monthly Salary</Trans>
          </Typography>

          <Typography>
            <FormattedSalary job={job} isMonthly hidePerName />
          </Typography>
        </div>
      </div>

      <LabeledItem
        label={t`Bonus System`}
        value={job.bonusSystem}
        className={styles.topGap}
      />

      <hr className={styles.topGap} />

      <div className={classnames([styles.rowWrapper])}>
        <LabeledItem
          label={t`Probation Period (months)`}
          value={job.probationPeriodMonths}
        />
        <LabeledItem label={t`Work Location`} value={job.location} />
        <LabeledItem label={t`Working Hours`} value={job.workingHours} />
        <LabeledItem label={t`Break Time (min)`} value={job.breakTimeMins} />
      </div>

      <div className={classnames([styles.rowWrapper, styles.topGap])}>
        <LabeledItem
          label={t`Flextime Eligibility`}
          value={getChoiceName(jobFlextimeEligibilityChoices, job.flexitimeEligibility)}
        />
        <LabeledItem
          label={t`Telework Eligibility`}
          value={getChoiceName(jobTeleworkEligibilityChoices, job.teleworkEligibility)}
        />
        <LabeledItem label={t`Overtime Conditions`} value={job.overtimeConditions} />
        <div />
      </div>

      <div className={classnames([styles.rowWrapper, styles.topGap])}>
        <LabeledItem label={t`Paid Leave Days (Annual)`} value={job.paidLeaves} />
        <LabeledItem label={t`Additional Leaves`} value={job.additionalLeaves} />
      </div>

      <hr className={styles.topGap} />

      <div
        className={classnames([styles.rowWrapper, styles.threeElements, styles.topGap])}
      >
        <LabeledItem
          label={t`Social Insurances`}
          value={getSeparatedString(socialInsurancesChoices, job.socialInsurances)}
        />
        <LabeledItem
          label={t`Commutation Allowance`}
          value={job.commutationAllowance}
        />
        <LabeledItem
          label={t`Other Benefits`}
          value={getSeparatedString(otherBenefitsChoices, job.otherBenefits)}
        />
      </div>
    </FormSection>
  );
};

JobConditions.propTypes = {
  job: PropTypes.object.isRequired,
};

export default memo(JobConditions);
