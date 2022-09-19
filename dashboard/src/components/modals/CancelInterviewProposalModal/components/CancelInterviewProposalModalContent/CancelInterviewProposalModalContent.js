import React, { useContext } from 'react';

import PropTypes from 'prop-types';
import { t, Trans } from '@lingui/macro';

import {
  Button,
  FormContextField,
  FormSection,
  FormSubsection,
  Modal,
  TimeslotDisplay,
  Typography,
} from '@components';
import { FormContext } from '@contexts';

import styles from './CancelInterviewProposalModalContent.module.scss';

function CancelInterviewProposalModalContent(props) {
  const { onSubmit } = useContext(FormContext);
  const { timeslots, isOpen, onClose } = props;

  return (
    <Modal
      title={t`Cancel Interview Proposal`}
      isOpen={isOpen}
      onClose={onClose}
      customButtons={
        <>
          <Button variant='secondary' color='danger' onClick={onSubmit}>
            <Trans>Cancel Interview Proposal</Trans>
          </Button>
          <Button variant='secondary' onClick={onClose}>
            <Trans>Cancel</Trans>
          </Button>
        </>
      }
    >
      <FormSection noBorder>
        <FormSubsection isGrid columnCount={1}>
          <Typography>
            <Trans>Are you sure you want to cancel this Interview Proposal?</Trans>
          </Typography>
          <div>
            {timeslots?.map?.((timeslot) => (
              <TimeslotDisplay
                className={styles.timeslot}
                key={timeslot.id}
                timeslot={timeslot}
              />
            ))}
          </div>
        </FormSubsection>
        <FormSubsection>
          <FormContextField
            withoutCapitalize
            label={t`Message (shown if candidate clicks on the proposal link)`}
            name='preScheduleMsg'
            type='rich-editor'
          />
        </FormSubsection>
        <FormSubsection>
          <Typography className={styles.note}>
            <Trans>
              Once you cancel, the interview proposal link will no longer be valid. If
              you want to reschedule the interview, you must send a new interview
              proposal to the candidate.
            </Trans>
          </Typography>
        </FormSubsection>
      </FormSection>
    </Modal>
  );
}

CancelInterviewProposalModalContent.propTypes = {
  timeslots: PropTypes.arrayOf(
    PropTypes.shape({
      startAt: PropTypes.instanceOf(Date),
      endAt: PropTypes.instanceOf(Date),
    })
  ),
  isOpen: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
};

export default CancelInterviewProposalModalContent;
