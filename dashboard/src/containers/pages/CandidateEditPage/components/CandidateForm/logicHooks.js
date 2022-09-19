import React, { useCallback, useMemo, useState } from 'react';
import { useHistory, useLocation, useParams } from 'react-router-dom';
import { useSelector } from 'react-redux';

import { v4 as uuid } from 'uuid';
import _ from 'lodash';
import { t } from '@lingui/macro';

import MissingInformation from '@components/modals/MissingInformation/MissingInformation';
import { client } from '@client';
import { ButtonBar, Typography } from '@components';
import {
  confirmArchivingCandidate,
  delay,
  fetchErrorHandler,
  makeCheckForDuplicationBeforeSave,
  addFieldRow,
  removeFieldRow,
  getMissingFields,
  openAlert,
  openConfirm,
  openMissingInformation,
} from '@utils';

import {
  Attachments,
  CandidateExpectations,
  CandidateManagement,
  Contact,
  CurrentEmployment,
  EducationDetails,
  ExperienceDetails,
  Metadata,
  Personal,
  SkillsAndExperience,
} from '../sections';
import * as handlers from './handlers';
import { initialFormState, SALARY_FIELDS } from './constants';

import styles from './CandidateForm.module.scss';

const useArchiving = () => {
  const history = useHistory();
  const { candidateId } = useParams();

  const showCannotBeArchived = useCallback(() => {
    openAlert({
      title: t`Alert`,
      description: t`This candidate has been proposed for a job and cannot be archived.`,
    });
  }, []);

  return useCallback(
    async (form) => {
      if (form.proposedToJob) {
        showCannotBeArchived();
      } else {
        try {
          await confirmArchivingCandidate();
          await client.execute({
            operationId: 'candidate_archive',
            parameters: { id: candidateId, data: {} },
          });

          history.push('/candidates');
        } catch (error) {
          const response = error.response;
          if (response) {
            if (response.status === 409 && _.get(response, 'obj.proposedToJob', null)) {
              await delay(300);
              showCannotBeArchived();
            } else {
              fetchErrorHandler(error);
            }
          }
        }
      }
    },
    [candidateId, history, showCannotBeArchived]
  );
};

const useDuplicating = () => {
  const [isDuplicate, setIsDuplicate] = useState(false);

  const { candidateId } = useParams();
  const history = useHistory();

  const setNotDuplicate = useCallback(async () => {
    try {
      await client.execute({
        operationId: 'candidates_partial_update',
        parameters: {
          id: candidateId,
          data: {
            original: null,
          },
        },
      });

      setIsDuplicate(false);
    } catch (error) {
      fetchErrorHandler(error);
    }
  }, [candidateId]);

  const proposeToSetAsNotDuplicate = useCallback(async () => {
    try {
      await openConfirm({ title: t`Are you sure this is not a duplicate` });
      await setNotDuplicate();
    } catch {} //eslint-disable-line no-empty
  }, [setNotDuplicate]);

  const checkDuplication = makeCheckForDuplicationBeforeSave(() => ({
    id: candidateId,
    redirect: history.push,
  }));

  return {
    isDuplicate,
    setIsDuplicate,
    proposeToSetAsNotDuplicate,
    checkDuplication,
  };
};

const useFormProcessing = ({ setIsDuplicate, checkDuplication }) => {
  const history = useHistory();
  const { returningPath } = useLocation();
  const { candidateId: editId } = useParams();

  const owner = useSelector((state) => state.user.id);

  const initialState = useMemo(
    () =>
      editId
        ? { ...initialFormState, scrapeData: false }
        : { ...initialFormState, owner },
    [editId, owner]
  );

  const endpoints = useMemo(() => {
    const endpointSuffix = editId ? 'partial_update' : 'create';

    return {
      save: `candidates_${endpointSuffix}`,
      read: 'candidates_read',
      validate: `candidates_validate_${endpointSuffix}`,
    };
  }, [editId]);

  const stateBoundHandlers = useMemo(
    () => ({
      addFieldRow,
      removeFieldRow,
    }),
    []
  );

  const processReadObject = useCallback(
    (candidate) => {
      setIsDuplicate(candidate.original != null);

      SALARY_FIELDS.forEach((key) => {
        if (candidate[key] === null) candidate[key] = '';
      });

      // collect all resume in one field 'allResume'
      const getResume = (ftype, file) => ({
        id: editId,
        localId: uuid(),
        ftype,
        file,
        error: false,
      });

      const allResume = [];
      const { resume, resumeJa, cvJa } = candidate;
      if (resume) allResume.push(getResume('resume', resume));
      if (resumeJa) allResume.push(getResume('resumeJa', resumeJa));
      if (cvJa) allResume.push(getResume('cvJa', cvJa));

      // need to add ID since it's not provided from backend
      const assignLocalId = (data) =>
        data.map((el) => ({
          ...el,
          localId: uuid(),
        }));

      return {
        ...candidate,
        experienceDetails: assignLocalId(candidate.experienceDetails),
        educationDetails: assignLocalId(candidate.educationDetails),
        source: candidate.source || null,
        allResume,
      };
    },
    [editId, setIsDuplicate]
  );

  const checkFormStateBeforeSave = useCallback(
    async (form, patchForm, resetFormState, handleSaveError) => {
      // validate empty, but not required field
      try {
        const emptyFields = getMissingFields({ form });

        if (emptyFields.length) {
          await openMissingInformation({
            title: t`Missing Information`,
            content: <MissingInformation emptyFields={emptyFields} />,
          });
        }
      } catch (error) {
        return;
      }

      // server validation
      try {
        const parameters = { data: form };
        if (editId) parameters.id = editId;

        await client.execute({
          operationId: endpoints.validate,
          parameters,
        });
      } catch (error) {
        handleSaveError(error);
        if (error?.response?.status === 400 && !form.importSource) return false;
      }

      // validate resume
      const resumeHaveTypes = form.allResume.every((resume) => Boolean(resume.ftype));
      if (!resumeHaveTypes) {
        handleSaveError(new Error(t`You must select a Type`), 'resumeError');
        return false;
      }

      if (!editId) return await checkDuplication(form, patchForm, resetFormState);

      return true;
    },
    [checkDuplication, editId, endpoints.validate]
  );

  const onSubmitDone = useCallback(async (...props) => {
    /**
     * send update requests only after all save requests are successful
     * this is needed because if, for example, saving files has errors,
     * but updating is successful user will be redirected and will not see errors from saving
     */
    const isSuccess = await handlers.saveFiles(...props);
    if (isSuccess) await handlers.updateFiles(...props);
  }, []);

  const onFormSave = useCallback(
    (candidate, formState) => {
      if (formState.scrapeData && candidate.linkedinUrl) {
        window.postMessage({ type: 'EXT_OPEN_PAGE', url: candidate.linkedinUrl }, '*');
      }

      const path = returningPath || `/candidate/${candidate.id}`;
      history.push(path);
    },
    [history, returningPath]
  );

  return {
    initialState,
    endpoints,
    stateBoundHandlers,
    processReadObject,
    checkFormStateBeforeSave,
    onSubmitDone,
    onFormSave,
  };
};

const useGetElements = (title) => {
  const history = useHistory();
  const { candidateId } = useParams();
  const { returningPath } = useLocation();

  const renderHeader = useCallback(
    () => (
      <Typography variant='h1' className={styles.title}>
        {title}
      </Typography>
    ),
    [title]
  );

  const renderInputs = useCallback(
    ({ form, FormInput, handlers, setValue, errors }) => {
      const { addFieldRow, removeFieldRow } = handlers;
      const {
        otherDesiredBenefits,
        educationDetails,
        experienceDetails,
        source,
        platform,
      } = form;

      return (
        <>
          <Personal {...{ FormInput }} />

          <Contact {...{ FormInput }} />

          <CurrentEmployment {...{ FormInput }} />

          <SkillsAndExperience
            {...{ form, FormInput, setValue, addFieldRow, removeFieldRow }}
          />

          <CandidateExpectations {...{ otherDesiredBenefits, FormInput, setValue }} />

          <ExperienceDetails
            data={experienceDetails}
            {...{ FormInput, addFieldRow, removeFieldRow }}
          />

          <EducationDetails
            data={educationDetails}
            {...{ FormInput, addFieldRow, removeFieldRow }}
          />

          <CandidateManagement {...{ source, platform, FormInput, setValue }} />

          <Attachments form={form} setValue={setValue} errors={errors} />

          <Metadata {...{ form }} />
        </>
      );
    },
    []
  );

  const renderButtons = useCallback(
    (form, makeOnSubmit, { disabled }) => {
      const cancelHandler = () => {
        history.push(returningPath ?? `/candidate/${candidateId}`);
      };

      return (
        <ButtonBar
          className={styles.buttonBar}
          onSave={makeOnSubmit()}
          onCancel={cancelHandler}
          shouldShowCancelButton={Boolean(candidateId)}
          isDisabled={disabled}
        />
      );
    },
    [candidateId, history, returningPath]
  );

  return {
    header: renderHeader,
    inputs: renderInputs,
    buttons: renderButtons,
  };
};

export { useArchiving, useDuplicating, useFormProcessing, useGetElements };
