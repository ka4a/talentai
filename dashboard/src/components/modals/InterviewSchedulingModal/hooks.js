import React, { useCallback, useMemo } from 'react';

import moment from 'moment';
import { t } from '@lingui/macro';
import cloneDeep from 'lodash/cloneDeep';

import { ButtonBar } from '@components';
import { INTERVIEW_STATUSES, INTERVIEW_SCHEDULING_TYPES } from '@constants';
import { useProposalsList, useProposalsRead } from '@swrAPI';

import Inputs from './components/Inputs';

const calculateDate = (date, time) => {
  if (!date || !time) return null;

  return moment(date)
    .set({ hours: time.getHours(), minutes: time.getMinutes() })
    .toISOString();
};

const toDatetimeRange = ({ startTime, endTime, date }) => ({
  startAt: calculateDate(date, startTime),
  endAt: calculateDate(date, endTime),
});

const toBackendTimeslot = (rawTimeslot) => {
  const timeslot = toDatetimeRange(rawTimeslot);
  timeslot.isRejected = false;
  return timeslot;
};

export function useProcessFormState(proposalId) {
  return useCallback(
    (form) =>
      form.schedulingType === INTERVIEW_SCHEDULING_TYPES.interviewProposal
        ? toProposeScheduleForm(form, proposalId)
        : toScheduleForm(form),
    [proposalId]
  );
}

function toScheduleForm(form) {
  const formCopy = cloneDeep(form);

  delete formCopy.timeslots;

  const currentTimeslot =
    form.schedulingType === INTERVIEW_SCHEDULING_TYPES.pastScheduling
      ? form.pastTimeslot
      : form.sourceTimeslots[0];

  return {
    ...formCopy,
    ...toDatetimeRange(currentTimeslot),
    status: INTERVIEW_STATUSES.scheduled,
  };
}

function toProposeScheduleForm(form, proposalId) {
  const formCopy = cloneDeep(form);
  const rejectedTimeslots = formCopy.timeslots.filter(
    (timeslot) => timeslot.isRejected
  );

  const timeslots = formCopy.sourceTimeslots
    .map(toBackendTimeslot)
    .concat(rejectedTimeslots);

  delete formCopy.sourceTimeslots;

  return {
    ...formCopy,
    status: INTERVIEW_STATUSES.pending,
    proposal: proposalId,
    timeslots,
  };
}

export function useProcessReadObject(candidate) {
  const isFromAgency = candidate?.source === 'Agency';
  const hasEmail = Boolean(candidate?.email);

  const canProposeSchedule = !isFromAgency && hasEmail;

  return useCallback(
    (interview) => ({
      ...interview,
      interviewer: interview?.interviewer?.id ?? null,
      schedulingType:
        interview?.schedulingType || getDefaultSchedulingType(canProposeSchedule),
    }),
    [canProposeSchedule]
  );
}

const getDefaultSchedulingType = (canProposeSchedule) =>
  canProposeSchedule
    ? INTERVIEW_SCHEDULING_TYPES.interviewProposal
    : INTERVIEW_SCHEDULING_TYPES.simpleScheduling;

export function useOnSaved(closeModal) {
  const refreshProposal = useProposalsRead().mutate;
  const refreshProposalsList = useProposalsList().mutate;

  return useCallback(async () => {
    closeModal();
    await Promise.all([refreshProposal(), refreshProposalsList()]);
  }, [closeModal, refreshProposal, refreshProposalsList]);
}

export function useRenderInputs(candidate) {
  const notAgencyCandidate = candidate?.source !== 'Agency';
  const hasEmail = Boolean(candidate?.email);

  return useCallback(
    ({ form, FormInput, setValue, errors, handlers }) => (
      <Inputs
        notAgencyCandidate={notAgencyCandidate}
        hasEmail={hasEmail}
        form={form}
        FormInput={FormInput}
        handlers={handlers}
        errors={errors}
        setValue={setValue}
      />
    ),
    [notAgencyCandidate, hasEmail]
  );
}

export function useRenderButtons(closeModal) {
  return useCallback(
    (form, makeOnSubmit, { disabled }) => (
      <ButtonBar
        onSave={makeOnSubmit()}
        onCancel={closeModal}
        isDisabled={disabled}
        saveText={getSaveButtonText(form.schedulingType)}
        isModal
      />
    ),
    [closeModal]
  );
}

// function is used instead of dictionary,
// because strings need to be translated according to chosen language
function getSaveButtonText(scheduleType) {
  switch (scheduleType) {
    case INTERVIEW_SCHEDULING_TYPES.interviewProposal:
      return t`Send Schedule Proposal`;
    case INTERVIEW_SCHEDULING_TYPES.simpleScheduling:
      return t`Send Invitation`;
    default:
      return t`Save`;
  }
}

export function useSchedulingTypeChoices(canProposeTimeslots) {
  return useMemo(() => {
    const simpleScheduling = {
      value: INTERVIEW_SCHEDULING_TYPES.simpleScheduling,
      name: t`Simple Scheduling (Candidate has been invited outside ZooKeep)`,
    };

    const pastScheduling = {
      value: INTERVIEW_SCHEDULING_TYPES.pastScheduling,
      name: t`Past Scheduling (Record an interview that already took place)`,
    };

    if (!canProposeTimeslots) return [simpleScheduling, pastScheduling];

    const interviewProposal = {
      value: INTERVIEW_SCHEDULING_TYPES.interviewProposal,
      name: t`Interview Proposal (Send interview time slots to Candidate)`,
    };

    return [interviewProposal, simpleScheduling, pastScheduling];
  }, [canProposeTimeslots]);
}
