import React, { memo } from 'react';
import { useParams } from 'react-router-dom';
import { Alert } from 'reactstrap';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { SectionsMenu, SwaggerForm, WindowBackground } from '@components';

import {
  useArchiving,
  useDuplicating,
  useFormProcessing,
  useGetElements,
} from './logicHooks';
import * as handlers from './handlers';
import { SECTIONS } from './constants';

import styles from './CandidateForm.module.scss';

const CandidateForm = ({ title }) => {
  const { candidateId: editId } = useParams();

  // currently is not being used
  const onArchiveCandidate = useArchiving(); // eslint-disable-line no-unused-vars

  const {
    isDuplicate,
    setIsDuplicate,
    proposeToSetAsNotDuplicate,
    checkDuplication,
  } = useDuplicating();

  const {
    initialState,
    endpoints,
    stateBoundHandlers,
    processReadObject,
    checkFormStateBeforeSave,
    onSubmitDone,
    onFormSave,
  } = useFormProcessing({
    setIsDuplicate,
    checkDuplication,
  });

  const { header, inputs, buttons } = useGetElements(title);

  return (
    <div>
      <div className={styles.wrapper}>
        <WindowBackground className={styles.formContainer}>
          <SwaggerForm
            formId='candidateForm'
            initialState={initialState}
            editing={editId}
            // api endpoints
            operationId={endpoints.save}
            readOperationId={endpoints.read}
            validateOperationId={endpoints.validate}
            // form processing handlers
            processFormState={handlers.processFormState}
            processReadObject={processReadObject}
            checkFormStateBeforeSave={checkFormStateBeforeSave}
            onFormSubmitDone={onSubmitDone}
            onSaved={onFormSave}
            handlers={stateBoundHandlers}
            // elements render
            formTop={header}
            inputs={inputs}
            buttons={buttons}
          />
        </WindowBackground>

        <SectionsMenu sections={SECTIONS} />
      </div>

      <div className={styles.alert}>
        <Alert color='warning' isOpen={isDuplicate}>
          <Trans>
            Duplicate Candidate: This candidate may be a duplicate. If this is not the
            case, please{' '}
            <button onClick={proposeToSetAsNotDuplicate}>click here</button>.
          </Trans>
        </Alert>
      </div>
    </div>
  );
};

CandidateForm.propTypes = {
  title: PropTypes.string.isRequired,
};

export default memo(CandidateForm);
