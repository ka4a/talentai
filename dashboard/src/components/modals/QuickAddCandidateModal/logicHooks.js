import React, { useCallback, useMemo } from 'react';
import { useSelector } from 'react-redux';

import { t } from '@lingui/macro';
import differenceBy from 'lodash/differenceBy';

import {
  clearNumberStr,
  getMissingFields,
  getNewResumeRequests,
  makeSaveFilesForForm,
  openMissingInformation,
} from '@utils';
import { client } from '@client';
import { ButtonBar, FormSection, MissingInformation } from '@components';

import {
  CandidateManagement,
  Contact,
  CurrentEmployment,
  Personal,
  Resume,
} from './sections';

import styles from './QuickAddCandidateModal.module.scss';

const initialFormState = {
  // personal
  firstName: '',
  lastName: '',
  firstNameKanji: '',
  lastNameKanji: '',

  // contact
  email: '',
  phone: '',

  // current employment
  currentCompany: '',
  currentPosition: '',
  currentSalaryCurrency: 'JPY',
  currentSalary: '',
  currentSalaryVariable: '',

  // candidate management
  source: '',
  sourceDetails: '',
  owner: null,

  // attachments
  allResume: [],
  resumeError: null,
};

const endpoints = {
  read: 'candidates_read',
  save: 'candidates_create',
  validate: 'candidates_validate_create',
};

export const saveFiles = makeSaveFilesForForm(
  ({ allResume, name }) =>
    getNewResumeRequests({
      allResume,
      name,
      operationId: 'candidates_upload_file',
    }),
  (newFiles, state) => {
    const oldResume = differenceBy(state.allResume, newFiles, 'ftype');

    return newFiles.reduce(
      (patch, upload) => {
        patch.allResume.push(upload.file);
        return patch;
      },
      { allResume: [...oldResume] }
    );
  }
);

export const useGetElements = (closeModal) => {
  const renderInputs = useCallback(
    ({ form, FormInput, setValue }) => (
      <div className={styles.wrapper}>
        <FormSection>
          <Personal {...{ FormInput }} />
          <Contact {...{ FormInput }} />
          <CurrentEmployment {...{ FormInput }} />
          <CandidateManagement source={form.source} {...{ FormInput, setValue }} />
          <Resume {...{ form, setValue }} />
        </FormSection>
      </div>
    ),
    []
  );

  const renderButtons = useCallback(
    (form, makeOnSubmit, { disabled }) => (
      <ButtonBar
        onSave={makeOnSubmit()}
        onCancel={closeModal}
        isDisabled={disabled}
        isModal
      />
    ),
    [closeModal]
  );

  return { inputs: renderInputs, buttons: renderButtons };
};

export const useFormProcessing = (closeModal) => {
  const userId = useSelector((state) => state.user.id);

  const initialState = useMemo(
    () => ({
      ...initialFormState,
      owner: userId,
    }),
    [userId]
  );

  const processReadObject = useCallback((candidate) => {
    if (candidate.currentSalary === null) candidate.currentSalary = '';
  }, []);

  const processFormState = useCallback(
    (form) => ({
      ...form,
      source: form.source ?? undefined,
      currentSalary: clearNumberStr(form.currentSalary),
      currentSalaryVariable: clearNumberStr(form.currentSalaryVariable),
    }),
    []
  );

  const onSubmitDone = useCallback(
    async (...args) => {
      await saveFiles(...args);
      closeModal();
    },
    [closeModal]
  );

  const checkFormStateBeforeSave = useCallback(
    async (form, patchForm, resetFormState, handleSaveError) => {
      // validate empty, but not required field
      try {
        const emptyFields = getMissingFields({ form, withLanguages: false });

        if (emptyFields.length) {
          await openMissingInformation({
            title: t`Missing Information`,
            content: <MissingInformation emptyFields={emptyFields} />,
          });
        }
      } catch (error) {
        return false;
      }

      try {
        await client.execute({
          operationId: endpoints.validate,
          parameters: { data: form },
        });
      } catch (error) {
        handleSaveError(error);
        return false;
      }

      const resumeHaveTypes = form.allResume.every((resume) => Boolean(resume.ftype));

      if (!resumeHaveTypes) {
        handleSaveError(new Error(t`You must select a Type`), 'resumeError');
        return false;
      }

      return true;
    },
    []
  );

  return {
    initialState,
    endpoints,
    processReadObject,
    processFormState,
    checkFormStateBeforeSave,
    onSubmitDone,
  };
};
