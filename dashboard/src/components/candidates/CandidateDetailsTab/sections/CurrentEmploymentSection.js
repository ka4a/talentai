import React, { memo, useMemo } from 'react';

import classnames from 'classnames';
import { Trans, t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { EMPLOYMENT_CHOICES, TAX_EQUALIZATION_CHOICES } from '@constants';
import { formatNumber, getChoiceName } from '@utils';
import LabeledItem from '@components/UI/LabeledItem';
import Typography from '@components/UI/Typography';
import { ShowAuthenticated } from '@components/auth';
import { useGetCandidate } from '@swrAPI';
import { useTranslatedChoices } from '@hooks';

import { ROLES_WITH_FULL_CANDIDATE_ACCESS } from '../constants';

import styles from '../CandidateDetailsSection.module.scss';

const CurrentEmploymentSection = () => {
  const { data: candidate } = useGetCandidate();

  const { i18n } = useLingui();
  const employmentChoices = useTranslatedChoices(i18n, EMPLOYMENT_CHOICES);
  const taxEqualisationOptions = useTranslatedChoices(i18n, TAX_EQUALIZATION_CHOICES);

  const {
    currentCompany = '',
    currentPosition = '',
    currentSalary,
    currentSalaryCurrency,
    employmentStatus = '',
    currentSalaryVariable,
    totalAnnualSalary,
    taxEqualization,
    currentSalaryBreakdown,
  } = candidate;

  const employmentStatusLabel = useMemo(() => {
    return getChoiceName(employmentChoices, employmentStatus) ?? '';
  }, [employmentStatus, employmentChoices]);

  const renderSalaryInput = (label, value) => (
    <LabeledItem
      label={label}
      value={formatNumber({ value, currency: currentSalaryCurrency })}
    />
  );

  return (
    <div className={styles.wrapper}>
      <Typography variant='subheading' className={styles.title}>
        <Trans>Current Employment</Trans>
      </Typography>

      <div className={classnames(styles.row, styles.mb20)}>
        <LabeledItem label={t`Current Job Title`} value={currentPosition} />
        <LabeledItem label={t`Current Employer`} value={currentCompany} />
      </div>

      <ShowAuthenticated groups={ROLES_WITH_FULL_CANDIDATE_ACCESS}>
        <div className={classnames(styles.row, styles.withBorder)}>
          <LabeledItem label={t`Employment Type`} value={employmentStatusLabel} />
          <LabeledItem
            label={t`Tax Equalization`}
            value={getChoiceName(taxEqualisationOptions, taxEqualization)}
          />
        </div>

        <div className={classnames([styles.row, styles.salaryWrapper])}>
          {renderSalaryInput(t`Total Annual Salary`, totalAnnualSalary)}
          {renderSalaryInput(t`Current Annual Fixed`, currentSalary)}
          {renderSalaryInput(t`Current Annual Variable`, currentSalaryVariable)}
        </div>

        <LabeledItem label={t`Compensation Notes`} value={currentSalaryBreakdown} />
      </ShowAuthenticated>
    </div>
  );
};

export default memo(CurrentEmploymentSection);
