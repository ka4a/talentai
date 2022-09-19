import React from 'react';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import {
  FormSection,
  FormSubsection,
  TimezoneDisplay,
  InterviewNotificationRecipients,
} from '@components';
import { useStaffOptions } from '@swrAPI';
import ProposeTimeslots from '@components/modals/InterviewSchedulingModal/components/ProposeTimeslots';
import { INTERVIEW_SCHEDULING_TYPES } from '@constants';

import { useSchedulingTypeChoices } from '../hooks';
import NoEmailMessage from './NoEmailMessage';
import Timeslot from './Timeslot';
import RejectedTimeslots from './RejectedTimeslots';

import styles from '../InterviewSchedulingModal.module.scss';

const Inputs = (props) => {
  const {
    notAgencyCandidate,
    hasEmail,
    form,
    FormInput,
    handlers,
    errors,
    setValue,
  } = props;
  const { addFieldRow, removeFieldRow } = handlers;
  const { schedulingType } = form;

  const staffList = useStaffOptions();

  const canProposeTimeslots = Boolean(hasEmail && notAgencyCandidate);
  let schedulingTypeChoices = useSchedulingTypeChoices(canProposeTimeslots);

  const isPastSchedule = schedulingType === INTERVIEW_SCHEDULING_TYPES.pastScheduling;
  const isInterviewProposal =
    schedulingType === INTERVIEW_SCHEDULING_TYPES.interviewProposal;

  function renderTimeslot() {
    const commonTimeslotProps = { setValue, FormInput };

    switch (schedulingType) {
      case INTERVIEW_SCHEDULING_TYPES.interviewProposal:
        return (
          <ProposeTimeslots
            {...commonTimeslotProps}
            timeslots={form.sourceTimeslots}
            addFieldRow={addFieldRow}
            removeFieldRow={removeFieldRow}
            name='sourceTimeslots'
            errorName='timeslots[0]'
            noTimeslotsError={errors?.timeslots?.[0]}
          />
        );
      case INTERVIEW_SCHEDULING_TYPES.pastScheduling:
        return (
          <Timeslot
            {...commonTimeslotProps}
            forcePastDate
            timeslot={form.pastTimeslot}
            name='pastTimeslot'
          />
        );
      case INTERVIEW_SCHEDULING_TYPES.simpleScheduling:
        return (
          <Timeslot
            {...commonTimeslotProps}
            timeslot={form.sourceTimeslots[0]}
            name='sourceTimeslots[0]'
          />
        );
      default:
        return null;
    }
  }

  return (
    <FormSection className={styles.contentWrapper}>
      <FormSubsection>
        <RejectedTimeslots />
        {!hasEmail && <NoEmailMessage />}
        <FormInput
          label={t`Scheduling Type`}
          name='schedulingType'
          type='select'
          options={schedulingTypeChoices}
        />
      </FormSubsection>
      <FormSubsection>
        <TimezoneDisplay />
        {renderTimeslot()}
      </FormSubsection>
      <FormSubsection>
        <div className={styles.interviewer}>
          <FormInput
            type='select'
            label={t`Interviewer`}
            name='interviewer'
            options={staffList}
            required
          />
        </div>

        {!isPastSchedule && (
          <div className={styles.topGap}>
            <FormInput
              type='rich-editor'
              label={t`Interview Invitation Details`}
              name='notes'
            />
          </div>
        )}
      </FormSubsection>
      <FormSubsection>
        <InterviewNotificationRecipients
          title={
            isInterviewProposal
              ? t`Once the candidate confirms, an interview invitation will be sent to:`
              : t`An interview invitation will be sent to:`
          }
          schedulingType={schedulingType}
        />
      </FormSubsection>
    </FormSection>
  );
};

Inputs.propTypes = {
  form: PropTypes.shape({}).isRequired,
  FormInput: PropTypes.func.isRequired,
  setValue: PropTypes.func.isRequired,
  handlers: PropTypes.shape({
    addFieldRow: PropTypes.func,
    removeFieldRow: PropTypes.func,
  }).isRequired,
  notAgencyCandidate: PropTypes.bool,
  hasEmail: PropTypes.bool,
};

export default Inputs;
