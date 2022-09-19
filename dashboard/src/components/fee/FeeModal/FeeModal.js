import React, { memo, useCallback } from 'react';
import { Button } from 'reactstrap';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import FeeForm from '../FeeForm';
import SelfContainedModal from '../../modals/SelfContainedModal';

FeeModal.propTypes = {
  onSaved: PropTypes.func,
  onFetch: PropTypes.func,
  proposal: PropTypes.object,
  onClosed: PropTypes.func,
  jobContract: PropTypes.shape({
    id: PropTypes.number.isRequired,
    contractType: PropTypes.number.isRequired,
  }).isRequired,
};

function FeeModal(props) {
  const {
    noButton,
    proposal,
    onSaved,
    isOpen,
    setIsOpen,
    onFetch,
    onClosed,
    jobContract,
  } = props;
  const { canEditPlacement, canCreatePlacement } = proposal || {};

  const feeId = props.feeId || (proposal ? proposal.feeId : null);

  const renderTrigger = useCallback(
    (open) => {
      let buttonText;

      if (feeId != null) {
        buttonText = canEditPlacement ? (
          <Trans>Edit Placement Form</Trans>
        ) : (
          <Trans>Placement Form</Trans>
        );
      } else if (canCreatePlacement) {
        buttonText = <Trans>Submit a Placement Form</Trans>;
      }

      return buttonText ? (
        <Button color='primary' onClick={open}>
          {buttonText}
        </Button>
      ) : null;
    },
    [canEditPlacement, canCreatePlacement, feeId]
  );

  const renderHeader = useCallback(
    () => (
      <h2 className='mb-0'>
        {proposal ? (
          <Trans>{proposal.candidate.name} placement form</Trans>
        ) : (
          <Trans>Fee form</Trans>
        )}
      </h2>
    ),
    [proposal]
  );

  const renderContent = useCallback(
    (controls) => (
      <FeeForm
        feeId={feeId}
        proposal={proposal}
        jobContract={jobContract}
        onFetch={onFetch}
        onSaved={(isFinal) => {
          if (isFinal) controls.close();
          if (onSaved) onSaved(isFinal);
        }}
      />
    ),
    [proposal, onSaved, onFetch, feeId, jobContract]
  );

  return (
    <SelfContainedModal
      size='lg'
      setIsOpen={setIsOpen}
      isOpen={isOpen}
      onClosed={onClosed}
      renderTrigger={noButton ? null : renderTrigger}
      renderHeader={renderHeader}
      renderContent={renderContent}
    />
  );
}

export default memo(FeeModal);
