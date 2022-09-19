import React, { useCallback, useRef, useMemo, useState } from 'react';

import { t, Trans } from '@lingui/macro';
import omit from 'lodash/omit';

import HCaptcha from '@hcaptcha/react-hcaptcha';
import { client } from '@client';
import { ButtonBar, FormSection, Typography } from '@components';
import { getNewResumeRequests, makeSaveFilesForForm, showErrorToast } from '@utils';
import { HCAPTCHA_SITE_KEY } from '@constants';

import {
  Agreement,
  ContactSection,
  CurrentEmploymentSection,
  NameSection,
  OnlineProfilesSection,
  QuestionsSection,
  ResumeSection,
  SkillsSection,
} from './components';
import { INITIAL_STATE } from './constants';

import styles from './JobPostingApplicationForm.module.scss';

export const saveFiles = makeSaveFilesForForm(
  ({ allResume, firstName, lastName }) =>
    getNewResumeRequests({
      allResume,
      name: `${firstName} ${lastName}`,
      operationId: 'candidates_public_upload_file',
    }),
  (newFiles, state) => {
    return newFiles.reduce(
      (patch, upload) => {
        patch.allResume.push(upload.file);
        return patch;
      },
      { allResume: [...state.allResume] }
    );
  }
);

export const useFormProcessing = (jobPosting, setSubmittedEmail, postingType) => {
  const initialState = useMemo(
    () => ({
      ...INITIAL_STATE,
      questions: jobPosting.questions.map(({ id, text }) => ({
        id,
        question: text,
        answer: '',
      })),
    }),
    [jobPosting.questions]
  );

  const processFormState = useCallback(
    (form) => {
      return {
        job: jobPosting.jobId,
        posting: postingType,
        candidate: omit(form, ['questions', 'resumeError', 'isAgreed']),
        questions: form.questions.map(({ id, answer }) => ({
          jobQuestionId: id,
          answer,
        })),
        token: form.token,
      };
    },
    [jobPosting.jobId, postingType]
  );

  const checkFormStateBeforeSave = useCallback(
    async (form, patchForm, resetFormState, handleSaveError) => {
      try {
        await client.execute({
          operationId: 'proposals_validate_public_application',
          parameters: { data: form },
        });
      } catch (error) {
        if (error.response.obj) {
          error.response.obj = {
            ...error.response.obj.candidate,
            questions: error.response.obj.questions,
          };
        }

        handleSaveError(error);
        return false;
      }

      const resumeHaveTypes = form.candidate.allResume.every((resume) =>
        Boolean(resume.ftype)
      );

      if (!resumeHaveTypes) {
        handleSaveError(new Error(t`You must select a Type`), 'resumeError');
        return false;
      }

      return true;
    },
    []
  );

  const onSubmitDone = useCallback(
    async (callback, obj, formState, throwErrorMessage) => {
      await saveFiles(callback, obj.candidate, formState, throwErrorMessage);
      setSubmittedEmail(obj.candidate.email);
    },
    [setSubmittedEmail]
  );

  return {
    initialState,
    processFormState,
    checkFormStateBeforeSave,
    onSubmitDone,
  };
};

export const useGetElements = () => {
  const captchaRef = useRef(null);
  const [token, setToken] = useState(null);

  const onExpire = () => {
    showErrorToast(<Trans>hCaptcha Token Expired</Trans>, { autoClose: 5000 });
  };

  const onError = (err) => {
    showErrorToast(t`hCaptcha Error: ${err}`, { autoClose: 5000 });
  };

  const renderHeader = useCallback(
    () => (
      <Typography variant='h1' className={styles.title}>
        <Trans>Application</Trans>
      </Typography>
    ),
    []
  );

  const renderInputs = useCallback(
    (inputProperties) => {
      const {
        form,
        setValue,
        handlers: { addFieldRow, removeFieldRow },
        FormInput,
      } = inputProperties;

      return (
        <>
          <FormSection className={styles.inputsWrapper}>
            <NameSection FormInput={FormInput} />
            <ContactSection FormInput={FormInput} />
            <OnlineProfilesSection FormInput={FormInput} />
            <CurrentEmploymentSection FormInput={FormInput} />
            <SkillsSection
              {...{ form, FormInput, setValue, addFieldRow, removeFieldRow }}
            />
            <QuestionsSection FormInput={FormInput} questions={form.questions} />
            <ResumeSection form={form} setValue={setValue} />
          </FormSection>

          <Agreement FormInput={FormInput} />
          <div className={styles.hCaptchaWrapper}>
            <HCaptcha
              sitekey={HCAPTCHA_SITE_KEY}
              onVerify={setToken}
              onError={onError}
              onExpire={onExpire}
              ref={captchaRef}
              size='normal'
              reCaptchaCompat={false}
            />
          </div>
        </>
      );
    },
    [captchaRef]
  );

  const renderButtons = useCallback(
    (form, makeOnSubmit, { disabled }) => {
      const onSave = (event) => {
        captchaRef.current.resetCaptcha();
        makeOnSubmit({ token: token })(event);
      };
      return (
        <ButtonBar
          onSave={onSave}
          className={styles.buttonBar}
          saveText={t`Submit Application`}
          shouldShowCancelButton={false}
          isDisabled={disabled || !form.isAgreed || !token}
        />
      );
    },
    [token]
  );

  return {
    header: renderHeader,
    inputs: renderInputs,
    buttons: renderButtons,
  };
};
