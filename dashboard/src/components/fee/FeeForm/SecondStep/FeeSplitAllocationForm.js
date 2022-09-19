import React, { memo, useMemo, useCallback } from 'react';
import { Button } from 'reactstrap';

import PropTypes from 'prop-types';
import _ from 'lodash';
import { Trans } from '@lingui/macro';

import { useSwagger } from '@hooks';
import { makeSaveFilesForForm, processListUpload } from '@utils';

import SwaggerForm from '../../../SwaggerForm';
import ReqStatus from '../../../ReqStatus';
import { useFormTop } from '../hooks';
import ApprovalButtons from '../ApprovalButtons';
import FeeSplitAllocationFormContent from './FeeSplitAllocationFormContent';

FeeSplitAllocationForm.propTypes = {
  feeId: PropTypes.number,
  splitAllocationId: PropTypes.number,
  proposal: PropTypes.shape({
    canididate: PropTypes.shape({
      owner: PropTypes.number,
      leadConsultant: PropTypes.number,
      supportConsultant: PropTypes.number,
      activator: PropTypes.number,
    }),
  }),
  clientId: PropTypes.number,
  onPrev: PropTypes.func,
  onSaved: PropTypes.func,
};

const SUBMIT_FOR_APPROVAL_ATTRS = { feeStatus: 'pending' };

const renderInputs = (props) => <FeeSplitAllocationFormContent {...props} />;

const SPLITS = [
  'candidateOwnerSplit',
  'leadCandidateConsultantSplit',
  'supportConsultantSplit',
  'clientOriginatorSplit',
  'leadBdConsultantSplit',
  'activatorSplit',
];

function processValidationParams(form, path, defaultParams) {
  if (_.includes(SPLITS, path[0])) {
    // splits must be validated together to check sum
    return _.pick(form, SPLITS);
  }

  return defaultParams;
}

function useRenderButtons(onPrev) {
  return useCallback(
    (form, makeOnSubmit, defaultButtonAttrs) => {
      const isPending = form.feeStatus === 'pending';
      const isApproved = form.feeStatus === 'approved';

      return (
        <div className='d-flex justify-content-end'>
          <Button onClick={onPrev} color='secondary'>
            <Trans>Previous</Trans>
          </Button>
          {form.isEditable ? (
            <>
              <ApprovalButtons
                form={form}
                statusField='feeStatus'
                makeOnSubmit={makeOnSubmit}
              />

              {!isPending ? (
                <>
                  <Button
                    {...defaultButtonAttrs}
                    onClick={makeOnSubmit({}, { showToast: true, status: null })}
                    color={isPending ? 'primary' : 'secondary'}
                    className='ml-1'
                  >
                    <Trans>Save</Trans>
                  </Button>
                  {!isApproved ? (
                    <Button
                      {...defaultButtonAttrs}
                      onClick={makeOnSubmit(SUBMIT_FOR_APPROVAL_ATTRS, {
                        showToast: true,
                        isFinal: true,
                      })}
                      color={'primary'}
                      className='ml-1'
                    >
                      <Trans>Submit for Approval</Trans>
                    </Button>
                  ) : null}
                </>
              ) : null}
            </>
          ) : null}
        </div>
      );
    },
    [onPrev]
  );
}

const processReadObject = (form) => {
  form.files = [];
  if (form.file)
    form.files.push({
      id: form.id,
      file: form.file,
    });
  return form;
};

const saveFile = makeSaveFilesForForm(
  (state) =>
    state.newFiles.map((file) => ({
      file,
      operationId: 'fee_split_allocation_upload_file',
      getParams: (obj) => ({ id: obj.id, file: file.file }),
    })),
  (newFiles, state) =>
    newFiles.reduce(
      (patch, upload) => {
        processListUpload(upload, patch.files, patch.newFiles);
        return patch;
      },
      { newFiles: [], files: [...state.files] }
    )
);

const resetAfterSave = (form, initialState, obj) => ({
  ...initialState,
  ...obj,
});

function FeeSplitAllocationForm(props) {
  const {
    feeId,
    isEditable,
    splitAllocationId,
    title,
    proposal,
    clientId,
    onPrev,
    onSaved,
  } = props;

  const renderFormTop = useFormTop(proposal);

  const clientInfoSwagger = useSwagger('agency_client_info_read', { client: clientId });
  const clientInfo = clientInfoSwagger.obj;

  const renderButtons = useRenderButtons(onPrev);

  const handleSaved = useCallback(
    (obj, form, options) => {
      if (onSaved) onSaved(obj, options);
    },
    [onSaved]
  );

  const initialState = useMemo(() => {
    const result = {
      fee: feeId,
      isEditable,
      candidateOwner: null,
      candidateOwnerSplit: 0,
      leadCandidateConsultant: null,
      leadCandidateConsultantSplit: 0,
      supportConsultant: null,
      supportConsultantSplit: 0,
      leadBdConsultant: null,
      leadBdConsultantSplit: 0,
      clientOriginator: null,
      clientOriginatorSplit: 0,
      activator: null,
      activatorSplit: 0,
      candidateSource: null,
      files: [],
      newFiles: [],
    };

    if (proposal) {
      const { candidate } = proposal;
      result.candidateOwner = candidate.owner;
      result.leadCandidateConsultant = candidate.leadConsultant;
      result.supportConsultant = candidate.supportConsultant;
      result.activator = candidate.activator;
    }

    if (clientInfo) {
      result.clientOriginator = clientInfo.originator;
    }

    return result;
  }, [feeId, isEditable, proposal, clientInfo]);

  if (clientInfoSwagger.loading)
    return <ReqStatus loading={clientInfoSwagger.loading} />;

  const action = splitAllocationId ? 'partial_update' : 'create';

  return (
    <SwaggerForm
      resetAfterSave={resetAfterSave}
      title={title}
      formTop={renderFormTop}
      processReadObject={processReadObject}
      processValidationParams={processValidationParams}
      validateOperationId={`fee_split_allocation_validate_${action}`}
      readOperationId='fee_split_allocation_read'
      formId='splitAllocation'
      operationId={`fee_split_allocation_${action}`}
      editing={splitAllocationId}
      inputs={renderInputs}
      isDisabled={!isEditable}
      onFormSubmitDone={saveFile}
      onSaved={handleSaved}
      buttons={renderButtons}
      initialState={initialState}
    />
  );
}

export default memo(FeeSplitAllocationForm);
