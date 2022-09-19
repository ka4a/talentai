import React, { memo } from 'react';

import PropTypes from 'prop-types';
import { useLingui } from '@lingui/react';
import { t } from '@lingui/macro';

import { getFormattedDate } from '@utils';

import Field from './AgencyContractDetailsField';

import styles from './AgencyDirectory.module.scss';

const PLACEHOLDER = '-';

function AgencyContractDetails({ agency }) {
  const { contract, name } = agency;
  const { startAt, endAt, feeRate, feeCurrency, initialFee } = contract;

  const { i18n } = useLingui();

  return (
    <div className={styles.details}>
      <Field isWide title={i18n._(t`Agency`)}>
        {name}
      </Field>

      <Field title={i18n._(t`Contract Start Date`)}>{getFormattedDate(startAt)}</Field>

      <Field title={i18n._(t`Contract End Date`)}>
        <div>{getFormattedDate(endAt)}</div>
        <div>{contract.duration}</div>
      </Field>

      <Field title={i18n._(t`Initial Fee`)}>
        {initialFee != null && feeCurrency != null
          ? i18n.number(initialFee, {
              style: 'currency',
              currency: feeCurrency,
              currencyDisplay: 'symbol',
            })
          : PLACEHOLDER}
      </Field>

      <Field title={i18n._(t`Fee (rate)`)}>
        {feeRate
          ? Number(feeRate).toString() + ' %' /* Remove insignificant trailing zeros */
          : PLACEHOLDER}
      </Field>
    </div>
  );
}

AgencyContractDetails.propTypes = {
  agency: PropTypes.shape({
    name: PropTypes.string,
    contract: PropTypes.shape({
      startAt: PropTypes.string,
      endAt: PropTypes.string,
      feeRate: PropTypes.string,
      feeCurrency: PropTypes.string,
      initialFee: PropTypes.string,
    }),
  }).isRequired,
};
AgencyContractDetails.defaultProps = {};

export default memo(AgencyContractDetails);
