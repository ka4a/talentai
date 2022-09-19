import React, { useCallback, useMemo } from 'react';
import { useHistory, useParams } from 'react-router-dom';
import { useSelector } from 'react-redux';

import intersection from 'lodash/intersection';
import omit from 'lodash/omit';
import map from 'lodash/map';

import { Typography, ButtonBar } from '@components';
import { clearNumberStr, addFieldRow, removeFieldRow, isDialogConfirmed } from '@utils';

import {
  Details,
  JobConditions,
  Requirements,
  HiringProcess,
  Attachments,
  Metadata,
} from '../sections';
import { initialFormState, USERS_ALLOWED_TO_CHANGE_STATUS } from './constants';
import * as formHandlers from './handlers';
import openSeeJobPosting from './utils/openSeeJobPosting';

import styles from './JobForm.module.scss';

const useFormProcessing = () => {
  const { jobId: editId, clientId: clientIdParam } = useParams();
  const history = useHistory();

  const userId = useSelector((state) => state.user.id);

  const initialState = useMemo(
    () => ({
      ...initialFormState,
      owner: userId,
    }),
    [userId]
  );

  const endpoints = useMemo(
    () => ({
      save: editId ? 'jobs_partial_update' : 'jobs_create',
      read: 'jobs_read',
      validate: editId
        ? 'jobs_validation_validate_partial_update'
        : 'jobs_validation_validate_partial_create',
    }),
    [editId]
  );

  const stateBoundHandlers = useMemo(
    () => ({
      addFieldRow,
      removeFieldRow,
      setOpeningsCount: formHandlers.setOpeningsCount,
    }),
    []
  );

  const clientId = Number.parseInt(clientIdParam, 10) || null;

  const processFormState = useCallback(
    (form) => {
      const omitLocalId = (data = []) => data.map((el) => omit(el, 'localId'));

      const newForm = {
        ...form,
        newFiles: null,
        agencies: map(form.agencies, 'id'),
        salaryFrom: clearNumberStr(form.salaryFrom),
        salaryTo: clearNumberStr(form.salaryTo),
        requiredLanguages: omitLocalId(form.requiredLanguages),
        questions: omitLocalId(form.questions),
        interviewTemplates: omitLocalId(form.interviewTemplates),
        hiringCriteria: omitLocalId(form.hiringCriteria),
        targetHiringDate: form.targetHiringDate || null,
        probationPeriodMonths: form.probationPeriodMonths || null,
        breakTimeMins: form.breakTimeMins || null,
        paidLeaves: form.paidLeaves || null,
        recruiters: form.recruiters.map((el) => el.recruiter),
      };

      if (clientId) newForm.client = clientId;

      return newForm;
    },
    [clientId]
  );

  const onSubmitDone = useCallback(async (callback, ...rest) => {
    /**
     * send update requests only after all save requests are successful
     * this is needed because if, for example, saving files has errors,
     * but updating is successful user will be redirected and will not see errors from saving
     */

    await formHandlers.saveFiles(maybeUpdateFiles, ...rest);

    function maybeUpdateFiles(success, savePatch) {
      if (!success) {
        callback(success, savePatch);
        return;
      }

      formHandlers.updateFiles(
        (success, updatePatch) => callback(success, { ...savePatch, ...updatePatch }),
        ...rest
      );
    }
  }, []);

  const onSaved = useCallback(
    async (job) => {
      let shouldGoToPostings = false;
      if (job.arePostingsOutdated) {
        shouldGoToPostings = await isDialogConfirmed(openSeeJobPosting());
      }
      const tab = shouldGoToPostings ? 'share' : '';
      history.push(`/job/${job.id}/${tab}`);
    },
    [history]
  );

  return {
    initialState,
    endpoints,
    stateBoundHandlers,
    processFormState,
    onSubmitDone,
    onSaved,
  };
};

const useGetElements = (title) => {
  const { jobId: editId } = useParams();
  const history = useHistory();

  const userId = useSelector((state) => state.user.id);

  const isAllowedToChangeStatus = useSelector((state) =>
    intersection(state.user.groups, USERS_ALLOWED_TO_CHANGE_STATUS)
  );

  const renderHeader = useCallback(
    () => (
      <Typography variant='h1' className={styles.title}>
        {title}
      </Typography>
    ),
    [title]
  );

  const renderInputs = useCallback(
    (inputProperties) => {
      const { form, setValue, handlers, FormInput } = inputProperties;

      const { setOpeningsCount, addFieldRow, removeFieldRow } = handlers;

      const disableReason = formHandlers.getDisableReason({
        form,
        userId,
        isAllowedToChangeStatus,
      });

      return (
        <>
          <Details {...{ FormInput }} />

          <Requirements
            {...{
              FormInput,
              form,
              setValue,
              addFieldRow,
              removeFieldRow,
            }}
          />

          <JobConditions {...{ FormInput }} />

          <HiringProcess
            {...{
              FormInput,
              disableReason,
              setOpeningsCount,
              setValue,
              form,
              addFieldRow,
              removeFieldRow,
            }}
          />

          <Attachments {...{ form, setValue }} />

          <Metadata {...{ FormInput, form }} />
        </>
      );
    },
    [isAllowedToChangeStatus, userId]
  );

  // different actions depend on if form is being created or edited
  const renderButtons = useCallback(
    (form, makeOnSubmit, { disabled }) => {
      const cancelHandler = () => {
        history.push(`/job/${editId}`);
      };

      return (
        <ButtonBar
          className={styles.buttonBar}
          onSave={makeOnSubmit({ published: true })}
          onCancel={cancelHandler}
          shouldShowCancelButton={Boolean(editId)}
          isDisabled={disabled}
        />
      );
    },
    [editId, history]
  );

  return {
    header: renderHeader,
    inputs: renderInputs,
    buttons: renderButtons,
  };
};

export { useFormProcessing, useGetElements };
