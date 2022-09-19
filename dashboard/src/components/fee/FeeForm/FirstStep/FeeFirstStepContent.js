import React, { memo, Component } from 'react';
import { Label } from 'reactstrap';
import { FormGroup, Col } from 'reactstrap';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import { compose } from 'redux';
import moment from 'moment';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';

import FormSection from '../../../SwaggerFormSection';
import LocaleOptionsProvider from '../../../LocaleOptionsProvider';
import FormLabeledContainer from '../../../FormLabeledContainer';
import BillDescriptionInputSet from '../../BillDescriptionInputSet';
import SourceSubForm from '../../../SubFormCandidateSource';
import BackendSearchSelectInput from '../../../SelectInput/BackendSearchSelectInput';

const wrapper = compose(memo, withI18n());

const getFullName = ({ firstName, lastName }) => `${firstName} ${lastName}`;

const LocalPropTypes = {
  component: PropTypes.oneOfType([PropTypes.func, PropTypes.instanceOf(Component)]),
};

function getQuarter(date) {
  const momentDate = moment(date);
  return momentDate.isValid() ? momentDate.format('[Q]Q YYYY') : '-';
}

FeeFirstStepContent.propTypes = {
  form: PropTypes.shape({
    shouldSendInvoiceEmail: PropTypes.bool,
    signedAt: PropTypes.string,
    startWorkAt: PropTypes.string,
    consultingFeeType: PropTypes.string,
  }).isRequired,
  isDisabled: PropTypes.func,
  setValue: PropTypes.func,
  FormInput: LocalPropTypes.component,
  FormInputBlock: LocalPropTypes.component,
  FormLabel: LocalPropTypes.component,
  i18n: PropTypes.shape({
    _: PropTypes.func.isRequired,
  }).isRequired,
};

const proposalToOption = (proposal) => ({
  label: getFullName(proposal.candidate),
  value: proposal.id,
});

function FeeFirstStepContent(props) {
  const {
    FormInputBlock,
    FormLabel,
    FormInput,
    i18n,
    form,
    setValue,
    isDisabled,
  } = props;

  const {
    consultingFeeType,
    shouldSendInvoiceEmail,
    signedAt,
    startsWorkAt,
    placement,
    contractType,
    nbvDate,
    nfiDate,
    billDescription,
    proposal,
    jobContract,
  } = form;

  const locale = useSelector((state) => state.settings.locale);

  const placeholders = {
    money: 'e.g. 500,000',
    date: i18n._(t`Select date`),
    title: i18n._(t`e.g. `),
  };

  return (
    <div className='pt-4'>
      {placement ? (
        <FormSection>
          <FormInputBlock
            type='formatted-number'
            name='placement.currentSalary'
            label={i18n._(t`Current Salary`)}
            placeholder={placeholders.money}
          />
          <FormInputBlock
            type='formatted-number'
            name='placement.offeredSalary'
            label={i18n._(t`Offered Salary`)}
            placeholder={placeholders.money}
          />
          <Col xs={12} md={6}>
            <FormGroup>
              <FormInput
                type='simple-datepicker'
                name='placement.signedAt'
                label={i18n._(t`Signed Date`)}
                placeholder={placeholders.date}
                locale={locale}
              />
            </FormGroup>
            <FormLabeledContainer isText label={i18n._(t`NBV Period`)}>
              {getQuarter(signedAt)}
            </FormLabeledContainer>
          </Col>
          <Col xs={12} md={6}>
            <FormGroup>
              <FormInput
                type='simple-datepicker'
                name='placement.startsWorkAt'
                label={i18n._(t`Start Work`)}
                placeholder={placeholders.date}
                locale={locale}
              />
            </FormGroup>
            <FormLabeledContainer isText label={i18n._(t`NFI Period`)}>
              {getQuarter(startsWorkAt)}
            </FormLabeledContainer>
          </Col>
          <SourceSubForm
            form={form}
            InputComponent={FormInputBlock}
            sourceField='placement.candidateSource'
            detailField='placement.candidateSourceDetails'
            setValue={setValue}
          />
        </FormSection>
      ) : (
        <FormSection>
          <Col xs={12} md={6}>
            <FormGroup>
              <FormInput
                type='simple-datepicker'
                name='nbvDate'
                label={i18n._(t`Contract Signed Date`)}
                placeholder={placeholders.date}
                locale={locale}
              />
            </FormGroup>
            <FormLabeledContainer isText label={i18n._(t`NBV Period`)}>
              {getQuarter(nbvDate)}
            </FormLabeledContainer>
          </Col>
          <Col xs={12} md={6}>
            <FormGroup>
              <FormInput
                type='simple-datepicker'
                name='nfiDate'
                label={i18n._(t`Retainer Fee`)}
                placeholder={placeholders.date}
                locale={locale}
              />
            </FormGroup>
            <FormLabeledContainer isText label={i18n._(t`NFI Period`)}>
              {getQuarter(nfiDate)}
            </FormLabeledContainer>
          </Col>
          <Col xs={12} md={6}>
            <FormGroup>
              <FormLabel name='proposal'>
                <Trans>Candidate</Trans>
              </FormLabel>
              <BackendSearchSelectInput
                disabled={isDisabled}
                operationId='proposals_list'
                name='proposal'
                toOption={proposalToOption}
                initialLabel={proposal != null ? getFullName(proposal.candidate) : null}
                value={form.proposalId}
                onSelect={(value) => setValue('proposalId', value)}
                params={{
                  job_contract: jobContract,
                  stage: 'shortlist',
                }}
                nullOption={i18n._(t`No Candidate`)}
              />
            </FormGroup>
          </Col>
        </FormSection>
      )}

      <FormSection title={i18n._(t`Client`)}>
        <FormInputBlock name='billingAddress' label={i18n._(t`Billing Address`)} />
        <Col xs={12} md={6}>
          <FormLabeledContainer
            label={i18n._(t`Invoice Email`)}
            rightFloat={
              <Label check>
                <FormInput type='checkbox' name='shouldSendInvoiceEmail' />
                <Trans>Send</Trans>
              </Label>
            }
          >
            <FormInput
              disabled={!shouldSendInvoiceEmail}
              name='invoiceEmail'
              placeholder='johndoe@example.com'
            />
          </FormLabeledContainer>
        </Col>
      </FormSection>
      <FormSection title={i18n._(t`Contract`)}>
        <LocaleOptionsProvider
          optionsKey='consultingFeeTypes'
          render={(options) => (
            <FormInputBlock
              label={i18n._(t`Consulting Fee Type`)}
              name='consultingFeeType'
              type='select'
              placeholder={i18n._(t`Select fee type`)}
              options={options}
            />
          )}
        />
        {consultingFeeType === 'fixed' ? (
          <FormInputBlock
            type='formatted-number'
            label={i18n._(t`Consulting Fee`)}
            name='consultingFee'
            placeholder='e.g. 5,000'
          />
        ) : null}
        {consultingFeeType === 'percentile' ? (
          <FormInputBlock
            type='percentage'
            label={i18n._(t`Consulting Fee Percentage`)}
            name='consultingFeePercentile'
            placeholder='e.g. 5%'
          />
        ) : null}
        <BillDescriptionInputSet
          name='billDescription'
          Input={FormInputBlock}
          isPlacementExists={placement != null}
          contractType={contractType}
          value={billDescription}
        />
      </FormSection>
      <FormSection title={i18n._(t`Invoice`)}>
        <FormInputBlock
          label={i18n._(t`Invoice Value`)}
          type='formatted-number'
          name='invoiceValue'
          placeholder={placeholders.money}
        />
        <FormInputBlock
          label={i18n._(t`Invoice Issuance Date`)}
          type='simple-datepicker'
          name='invoiceIssuanceDate'
          placeholder={placeholders.date}
        />
        <FormInputBlock
          label={i18n._(t`Invoice Due Date`)}
          type='simple-datepicker'
          name='invoiceDueDate'
        />
        <LocaleOptionsProvider
          optionsKey='invoiceStatuses'
          render={(options) => (
            <FormInputBlock
              label={i18n._(t`Invoice Status`)}
              type='select'
              name='invoiceStatus'
              options={options}
            />
          )}
        />
        {form.invoiceStatus === 'paid' ? (
          <FormInputBlock
            label={i18n._(t`Invoice Payment Date`)}
            type='simple-datepicker'
            name='invoicePaidAt'
          />
        ) : null}
      </FormSection>
      <FormSection title={i18n._(t`Additional Info`)}>
        <FormInputBlock
          xs={12}
          type='rich-editor'
          label={i18n._(t`Comments`)}
          name='notesToApprover'
        />
      </FormSection>
    </div>
  );
}

export default wrapper(FeeFirstStepContent);
