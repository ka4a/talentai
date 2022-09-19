import React, { useCallback } from 'react';
import { useSelector } from 'react-redux';
import { Row } from 'reactstrap';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

FormInputsJobAgencyContract.propTypes = {
  i18n: PropTypes.shape({
    _: PropTypes.func.isRequired,
  }).isRequired,
  form: PropTypes.shape({
    contractType: PropTypes.string,
    billDescription: PropTypes.string,
  }).isRequired,
  setValue: PropTypes.func.isRequired,
};

const wrapper = withI18n();

function FormInputsJobAgencyContract(props) {
  const { FormInputBlock, setValue, i18n, form } = props;

  const { contractType } = form;

  const contractTypeOptions = useSelector(
    (state) => state.settings.localeData.contractTypes
  );

  const industryOptions = useSelector((state) => state.settings.localeData.industries);

  const locale = useSelector((state) => state.settings.locale);

  const setContractType = useCallback(
    (event) => {
      const newValue = event.target.value;
      if (contractType !== newValue) {
        setValue('billDescription', null);
        setValue('contractType', newValue);
      }
    },
    [setValue, contractType]
  );

  return (
    <Row form>
      <FormInputBlock
        label={i18n._(t`Contact Person`)}
        type='text'
        name='contactPersonName'
        placeholder={i18n._(t`e.g John Smith`)}
      />

      <FormInputBlock
        label={i18n._(t`Industry`)}
        type='select'
        name='industry'
        placeholder={i18n._(t`Select industry`)}
        options={industryOptions}
      />
      <FormInputBlock
        label={i18n._(t`Contract Type`)}
        type='select'
        name='contractType'
        onChange={setContractType}
        options={contractTypeOptions}
        placeholder={i18n._(t`Select contract type`)}
      />
      <FormInputBlock
        label={i18n._(t`Signed at`)}
        type='simple-datepicker'
        name='signedAt'
        locale={locale}
        placeholder={i18n._(t`Select date`)}
      />
    </Row>
  );
}

export default wrapper(FormInputsJobAgencyContract);
