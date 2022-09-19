import React, { memo } from 'react';
import { useParams } from 'react-router-dom';

import PropTypes from 'prop-types';

import { SwaggerForm, SectionsMenu, WindowBackground } from '@components';

import { SECTIONS } from './constants';
import * as formHandlers from './handlers';
import { useFormProcessing, useGetElements } from './logicHooks';

import styles from './JobForm.module.scss';

const JobForm = ({ title }) => {
  const { jobId: editId } = useParams();

  const {
    initialState,
    endpoints,
    stateBoundHandlers,
    processFormState,
    onSubmitDone,
    onSaved,
  } = useFormProcessing();

  const { header, inputs, buttons } = useGetElements(title);

  return (
    <div className={styles.wrapper}>
      <WindowBackground className={styles.formContainer}>
        <SwaggerForm
          formId='jobForm'
          editing={editId}
          initialState={initialState}
          // api endpoints
          operationId={endpoints.save}
          readOperationId={endpoints.read}
          validateOperationId={endpoints.validate}
          // form processing handlers
          processFormState={processFormState}
          processReadObject={formHandlers.processReadObject}
          checkFormStateBeforeSave={formHandlers.checkFormStateBeforeSave}
          onFormSubmitDone={onSubmitDone}
          handlers={stateBoundHandlers}
          onSaved={onSaved}
          // elements render
          formTop={header}
          inputs={inputs}
          buttons={buttons}
        />
      </WindowBackground>

      <SectionsMenu sections={SECTIONS} />
    </div>
  );
};

JobForm.propTypes = {
  title: PropTypes.string.isRequired,
};

export default memo(JobForm);
