import React, { memo } from 'react';
import { Row } from 'reactstrap';
import Col from 'reactstrap/es/Col';

import PropTypes from 'prop-types';
import { compose } from 'redux';
import moment from 'moment-timezone';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import FormLabeledContainer from '../../FormLabeledContainer';
import LocaleOptionLabel from '../../LocaleOptionLabel';

FormPreviewJobAgencyContract.propTypes = {
  form: PropTypes.shape({
    contractType: PropTypes.string,
    industry: PropTypes.string,
    billDescription: PropTypes.string,
    contactPersonName: PropTypes.string,
    signedAt: PropTypes.string,
  }).isRequired,
  i18n: PropTypes.shape({
    _: PropTypes.func.isRequired,
  }).isRequired,
};

const wrapper = compose(memo, withI18n());

function FormPreviewJobAgencyContract(props) {
  const { i18n, form } = props;

  const { contactPersonName, contractType, industry, signedAt } = form;

  return (
    <div>
      <Row>
        <Col xs={12} md={6}>
          <FormLabeledContainer isCompact isText label={i18n._(t`Contact Person`)}>
            {contactPersonName}
          </FormLabeledContainer>
        </Col>
        <Col xs={12} md={6}>
          <FormLabeledContainer isCompact isText label={i18n._(t`Industry`)}>
            <LocaleOptionLabel optionsKey='industries' value={industry} />
          </FormLabeledContainer>
        </Col>
      </Row>
      <Row>
        <Col xs={12} md={6}>
          <FormLabeledContainer isCompact isText label={i18n._(t`Contract Type`)}>
            <LocaleOptionLabel optionsKey='jobContractTypes' value={contractType} />
          </FormLabeledContainer>
        </Col>
        <Col xs={12} md={6}>
          <FormLabeledContainer isCompact isText label={i18n._(t`Signed at`)}>
            {moment(signedAt).format('LL')}
          </FormLabeledContainer>
        </Col>
      </Row>
    </div>
  );
}

export default wrapper(FormPreviewJobAgencyContract);
