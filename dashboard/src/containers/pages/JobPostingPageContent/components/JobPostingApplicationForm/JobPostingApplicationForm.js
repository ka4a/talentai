import React, { memo } from 'react';

import PropTypes from 'prop-types';

import { SwaggerForm } from '@components';
import { addFieldRow, removeFieldRow } from '@utils';

import { useFormProcessing, useGetElements } from './hooks';

const stateBoundHandlers = { addFieldRow, removeFieldRow };

const JobPostingApplicationForm = ({
  jobPosting,
  showSuccessBox,
  setSubmittedEmail,
  postingType,
}) => {
  const {
    initialState,
    processFormState,
    checkFormStateBeforeSave,
    onSubmitDone,
  } = useFormProcessing(jobPosting, setSubmittedEmail, postingType);

  const { header, inputs, buttons } = useGetElements();

  return (
    <div id='application'>
      <SwaggerForm
        initialState={initialState}
        formId='jobPostingApplicationForm'
        // api endpoints
        operationId='proposals_public_application'
        // form processing handlers
        checkFormStateBeforeSave={checkFormStateBeforeSave}
        processFormState={processFormState}
        onFormSubmitDone={onSubmitDone}
        handlers={stateBoundHandlers}
        onSaved={showSuccessBox}
        // elements render
        formTop={header}
        inputs={inputs}
        buttons={buttons}
      />
    </div>
  );
};

JobPostingApplicationForm.propTypes = {
  showSuccessBox: PropTypes.func.isRequired,
  setSubmittedEmail: PropTypes.func.isRequired,
  postingType: PropTypes.string.isRequired,
  jobPosting: PropTypes.shape({
    jobId: PropTypes.number,
    questions: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number,
        text: PropTypes.string,
      })
    ).isRequired,
  }).isRequired,
};

export default memo(JobPostingApplicationForm);
