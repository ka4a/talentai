import React, { memo, useMemo } from 'react';

import { Trans } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { SALARY_PER_CHOICES } from '@constants';
import { formatNumber, getChoiceName } from '@utils';
import { useTranslatedChoices } from '@hooks';

const MONTH_AMOUNT = 12;

const FormattedSalary = (props) => {
  const { i18n } = useLingui();
  const salaryPerChoices = useTranslatedChoices(i18n, SALARY_PER_CHOICES);

  const {
    job = {},
    hidePerName = false,
    placeholder = null,
    single,
    isAnnual,
    isMonthly,
  } = props;
  const { salaryCurrency, salaryFrom, salaryTo, salaryPer, salary: salarySingle } = job;

  const salary = useMemo(() => {
    const getCalculatedSalary = (from, to) => ({ from, to });

    // calculate monthly salary based on annual
    if (salaryPer === 'year' && isMonthly) {
      return getCalculatedSalary(salaryFrom / MONTH_AMOUNT, salaryTo / MONTH_AMOUNT);
    }

    // calculate annual salary based on monthly
    if (salaryPer === 'month' && isAnnual) {
      return getCalculatedSalary(salaryFrom * MONTH_AMOUNT, salaryTo * MONTH_AMOUNT);
    }

    // default case
    return getCalculatedSalary(salaryFrom, salaryTo);
  }, [isAnnual, isMonthly, salaryFrom, salaryPer, salaryTo]);

  const getSalary = (localSalary) =>
    formatNumber({ value: localSalary, currency: salaryCurrency });

  if (salaryFrom === null && salaryTo === null) {
    return placeholder;
  }

  const salaryFromFormatted = getSalary(salary.from);
  const salaryToFormatted = getSalary(salary.to);
  const salarySingleFormatted = getSalary(salarySingle);

  const salaryPerName = salaryPer ? getChoiceName(salaryPerChoices, salaryPer) : '';

  if (single && job.salary) return salarySingleFormatted;

  let salaryStr;
  if (job.salaryFrom !== null && job.salaryTo !== null) {
    if (job.salaryFrom === job.salaryTo) {
      salaryStr = salaryFromFormatted;
    } else {
      salaryStr = (
        <span>
          {salaryFromFormatted}&nbsp;- {salaryToFormatted}
        </span>
      );
    }
  } else if (job.salaryFrom !== null) {
    salaryStr = (
      <span>
        <Trans>starting from</Trans> {salaryFromFormatted}
      </span>
    );
  } else {
    salaryStr = (
      <span>
        <Trans>up to</Trans> {salaryToFormatted}
      </span>
    );
  }

  return (
    <span>
      {salaryStr} {hidePerName ? null : ' ' + salaryPerName}
    </span>
  );
};

export default memo(FormattedSalary);
