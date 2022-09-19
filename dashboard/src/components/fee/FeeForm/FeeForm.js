import React, { memo, useState, useCallback } from 'react';

import PropTypes from 'prop-types';

import FeeFormFirstStep from './FirstStep/FeeFormFirstStep';
import FeeSplitAllocationForm from './SecondStep/FeeSplitAllocationForm';
import openSuccessToast from './openSuccessToast';

FeeForm.propTypes = {
  feeId: PropTypes.number,
  proposal: PropTypes.object,
  onSaved: PropTypes.func,
  onFetch: PropTypes.func,
  title: PropTypes.string,
  jobContract: PropTypes.shape({
    id: PropTypes.number.isRequired,
    contractType: PropTypes.string.isRequired,
  }).isRequired,
};

function FeeForm(props) {
  const { proposal, onSaved, onFetch, title, feeId, jobContract } = props;

  const [clientId, setClientId] = useState(null);

  const [step, setStep] = useState(1);
  const [feeState, setFeeState] = useState({
    id: feeId,
    splitAllocationId: null,
    isEditable: true,
  });

  const handleNext = useCallback(() => setStep(2), [setStep]);
  const handlePrev = useCallback(() => setStep(1), [setStep]);

  const handleFeeSaved = useCallback(
    (fee, options) => {
      setFeeState((state) => ({
        id: fee.id,
        splitAllocationId: fee.splitAllocationId,
        isEditable: state.isEditable,
      }));
      setClientId(fee.clientId);
      if (options.showToast) {
        openSuccessToast(proposal, options.status);
      }

      if (onSaved) onSaved(options.isFinal);
    },
    [onSaved, proposal]
  );

  const handleSplitAllocationSaved = useCallback(
    (allocation, options) => {
      setFeeState({
        id: allocation.fee,
        splitAllocationId: allocation.id,
        isEditable: allocation.isEditable,
      });

      if (options.showToast) {
        openSuccessToast(proposal, options.status);
      }

      if (onSaved) onSaved(options.isFinal);
    },
    [onSaved, proposal]
  );

  const handleFeeFetch = useCallback(
    (fee) => {
      setFeeState({
        id: fee.id,
        isEditable: fee.isEditable,
        splitAllocationId: fee.splitAllocationId,
      });
      setClientId(fee.clientId);
      if (onFetch) onFetch(fee);
    },
    [onFetch]
  );

  if (step === 2) {
    return (
      <FeeSplitAllocationForm
        title={title}
        clientId={clientId}
        isEditable={feeState.isEditable}
        feeId={feeState.id}
        splitAllocationId={feeState.splitAllocationId}
        proposal={proposal}
        onPrev={handlePrev}
        onSaved={handleSplitAllocationSaved}
      />
    );
  }

  return (
    <FeeFormFirstStep
      feeId={feeState.id}
      proposal={proposal}
      onNext={handleNext}
      onSaved={handleFeeSaved}
      onFetch={handleFeeFetch}
      title={title}
      jobContract={jobContract}
    />
  );
}

export default memo(FeeForm);
