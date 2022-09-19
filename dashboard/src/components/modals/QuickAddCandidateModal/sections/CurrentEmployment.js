import React from 'react';

import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';
import { useLingui } from '@lingui/react';

import { Typography } from '@components';
import { SALARY_CURRENCY_CHOICES } from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from '../QuickAddCandidateModal.module.scss';

const CurrentEmployment = ({ FormInput }) => {
  const { i18n } = useLingui();
  const salaryCurrencyChoices = useTranslatedChoices(
    i18n,
    SALARY_CURRENCY_CHOICES,
    'description'
  );

  return (
    <>
      <Typography
        variant='subheading'
        className={classnames([styles.subtitle, styles.topGap])}
      >
        <Trans>Current Employment</Trans>
      </Typography>

      <div className={classnames([styles.rowWrapper, styles.twoElements])}>
        <FormInput name='currentPosition' label={t`Current Job Title`} />
        <FormInput name='currentCompany' label={t`Current Company`} />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.threeElements, styles.topGap])}
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
          placeholder={t`e.g. 500,000`}
        />
        <FormInput
          type='formatted-number'
          name='currentSalaryVariable'
          label={t`Current Annual Variable`}
          placeholder={t`e.g. 500,000`}
        />
      </div>
    </>
  );
};

CurrentEmployment.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default CurrentEmployment;
