import React, { memo, useCallback, useMemo } from 'react';
import { Button } from 'reactstrap';
import { useSelector } from 'react-redux';

import _ from 'lodash';
import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { getFormattedDate } from '@utils';

import FeeFirstStepContent from './FeeFirstStepContent';
import SwaggerForm from '../../../SwaggerForm';
import { useFormTop } from '../hooks';

FeeFormFirstStep.propTypes = {
  i18n: PropTypes.shape({
    _: PropTypes.func.isRequired,
  }).isRequired,
  feeId: PropTypes.number,
  proposal: PropTypes.shape({
    feeId: PropTypes.number,
    id: PropTypes.number.isRequired,
    jobCreatedByName: PropTypes.string.isRequired,
    hiredAt: PropTypes.string.isRequired,
    candidate: PropTypes.shape({
      salary: PropTypes.number,
      targetSalary: PropTypes.number,
    }).isRequired,
    job: PropTypes.shape({
      title: PropTypes.string.isRequired,
      clientName: PropTypes.isRequired,
    }).isRequired,
  }),
  onSaved: PropTypes.func,
  onFetch: PropTypes.func,
  title: PropTypes.string,
  jobContract: PropTypes.shape({
    id: PropTypes.number,
    type: PropTypes.string,
  }),
};

const renderInputs = (contentProps) => <FeeFirstStepContent {...contentProps} />;

const useRenderButtons = (onNext) => {
  return useCallback(
    (form, makeOnSubmit, defaultButtonAttrs) => (
      <div className='d-flex justify-content-end'>
        {form.isEditable || form.id ? (
          <>
            <Button
              {...defaultButtonAttrs}
              onClick={form.isEditable ? makeOnSubmit() : onNext}
              color='primary'
              className='ml-1'
            >
              {form.isEditable ? <Trans>Save and Next</Trans> : <Trans>Next</Trans>}
            </Button>
          </>
        ) : null}
      </div>
    ),
    [onNext]
  );
};

const CONSULTING_FEE_OMIT_FIELDS = {
  fixed: ['consultingFeePercentile'],
  percentile: ['consultingFee'],
};

function omitUnusedConsultingFeeField(form) {
  const consultingFeeFieldToOmit = CONSULTING_FEE_OMIT_FIELDS[form.consultingFeeType];

  if (consultingFeeFieldToOmit) form = _.omit(form, consultingFeeFieldToOmit);

  return form;
}

const wrapper = memo;

function processFormState(form) {
  return omitUnusedConsultingFeeField(form);
}

const isFormDisabled = (form) => !form.isEditable;

function FeeFormFirstStep(props) {
  const { proposal, feeId, onNext, onSaved, title, onFetch, jobContract } = props;

  const handleSaved = useCallback(
    (placement, form, options) => {
      onSaved(placement, options);
      if (options.isFinal) return;
      onNext();
    },
    [onSaved, onNext]
  );

  const billDescriptionOptionGroups = useSelector(
    (state) => state.settings.localeData.billDescriptions
  );

  const initialState = useMemo(() => {
    const result = {
      status: 'draft',
      isEditable: true,
      industry: null,
      contactPersonName: '',
      billingAddress: '',
      shouldSendInvoiceEmail: false,
      invoiceEmail: '',
      consultingFeeType: 'fixed',
      consultingFee: '',
      consultingFeePercentile: 0,
      contractType: null,
      billDescription: null,
      invoiceValue: '',
      invoiceIssuanceDate: getFormattedDate(Date.now()),
      invoiceStatus: 'not_sent',
      iosIoa: '',
      notesToApprover: '',
    };

    if (jobContract) {
      result.jobContract = jobContract.id;
      result.contractType = jobContract.contractType;

      const isPlacementExist = proposal != null;

      const billDescriptionOptions =
        billDescriptionOptionGroups[jobContract.contractType];
      const billDescriptionOption = billDescriptionOptions.find(
        (option) => option.forPlacement === isPlacementExist
      );

      result.billDescription = _.get(billDescriptionOption, 'value');
      if (!isPlacementExist) {
        result.nbvDate = jobContract.signedAt;
      }
    }

    if (proposal) {
      const { id, candidate, hiredAt, jobCreatedByName } = proposal;
      result.placement = {
        proposal: id,
        currentSalary: candidate.currentSalary || '',
        offeredSalary: '',
        signedAt: getFormattedDate(hiredAt),
        startsWorkAt: null,
        candidateSource: null,
        candidateSourceDetails: '',
      };
      result.contactPersonName = jobCreatedByName;
    }

    return result;
  }, [proposal, jobContract, billDescriptionOptionGroups]);

  const isEditing = feeId != null;

  const renderFormTop = useFormTop(proposal);

  const renderButtons = useRenderButtons(onNext);

  const processReadObject = useCallback(
    (obj) => {
      if (onFetch) onFetch(obj);

      return omitUnusedConsultingFeeField(obj);
    },
    [onFetch]
  );

  return (
    <SwaggerForm
      resetAfterSave
      formTop={renderFormTop}
      title={title}
      readOperationId='fee_read'
      processReadObject={processReadObject}
      processFormState={processFormState}
      operationId={isEditing ? 'fee_partial_update' : 'fee_create'}
      isDisabled={isFormDisabled}
      editing={feeId}
      formId='feeForm'
      inputs={renderInputs}
      buttons={renderButtons}
      initialState={initialState}
      onSaved={handleSaved}
    />
  );
}

export default wrapper(FeeFormFirstStep);
