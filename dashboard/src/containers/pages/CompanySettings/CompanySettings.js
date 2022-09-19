import React, { memo } from 'react';

import { t } from '@lingui/macro';

import { DefaultPageContainer, SwaggerForm, WindowBackground } from '@components';

import { useGetElements, useFormProcessing } from './logicHooks';

import styles from './CompanySettings.module.scss';

const CompanySettings = () => {
  const {
    initialState,
    processReadObject,
    processFormState,
    onSubmitDone,
    checkFormStateBeforeSave,
  } = useFormProcessing();
  const { header, inputs, buttons } = useGetElements();

  return (
    <DefaultPageContainer title={t`Company Settings`}>
      <div className={styles.container}>
        <WindowBackground className={styles.formContainer}>
          <SwaggerForm
            editing
            formId='companySettingsForm'
            // endpoints
            readOperationId={OPERATION_IDS.read}
            operationId={OPERATION_IDS.partialUpdate}
            validateOperationId={OPERATION_IDS.validate}
            // form processing
            initialState={initialState}
            processFormState={processFormState}
            processReadObject={processReadObject}
            onFormSubmitDone={onSubmitDone}
            checkFormStateBeforeSave={checkFormStateBeforeSave}
            resetAfterSave
            // render elements
            formTop={header}
            inputs={inputs}
            buttons={buttons}
          />
        </WindowBackground>
      </div>
    </DefaultPageContainer>
  );
};

const OPERATION_IDS = {
  partialUpdate: 'clients_settings_partial_update',
  validate: 'clients_settings_validate_partial_update',
  read: 'clients_settings_read',
};

export default memo(CompanySettings);
