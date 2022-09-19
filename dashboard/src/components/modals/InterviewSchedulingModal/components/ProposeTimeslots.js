import React from 'react';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { Typography } from '@components';
import styles from '@components/modals/InterviewSchedulingModal/InterviewSchedulingModal.module.scss';
import TimeslotList from '@components/modals/InterviewSchedulingModal/components/TimeslotList';

function ProposeTimeslots(props) {
  const {
    timeslots,
    FormInput,
    addFieldRow,
    removeFieldRow,
    setValue,
    noTimeslotsError,
    name,
    errorName,
  } = props;

  return (
    <div>
      <Typography className={styles.bottomGap}>
        <Trans>
          Suggest a few time slots to find a common time with the candidate.
        </Trans>
      </Typography>

      <TimeslotList
        data={timeslots}
        FormInput={FormInput}
        addFieldRow={addFieldRow}
        removeFieldRow={removeFieldRow}
        setValue={setValue}
        name={name}
        errorName={errorName}
      />

      {noTimeslotsError && (
        <Typography variant='caption' className={styles.error}>
          <Trans>Please add at least one time slot</Trans>
        </Typography>
      )}
    </div>
  );
}

ProposeTimeslots.propTypes = {
  timeslots: PropTypes.array.isRequired,
  FormInput: PropTypes.elementType.isRequired,
  addFieldRow: PropTypes.func.isRequired,
  removeFieldRow: PropTypes.func.isRequired,
  setValue: PropTypes.func.isRequired,
  noTimeslotsError: PropTypes.bool,
  name: PropTypes.string.isRequired,
  errorName: PropTypes.string.isRequired,
};

export default ProposeTimeslots;
