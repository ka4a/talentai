import React, { useEffect, useMemo } from 'react';
import { usePrevious } from 'react-use';

import moment from 'moment';
import { t } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { formatSubfield } from '@utils';
import { TIME_FORMAT } from '@constants';

import styles from '../InterviewSchedulingModal.module.scss';

const TIME_INPUT_PROPS = {
  type: 'simple-datepicker',
  timeFormat: TIME_FORMAT.picker,
  dateInputFormat: TIME_FORMAT.picker,
  showTimeSelectOnly: true,
  showTimeSelect: true,
  timeCaption: '',
};

// this could create an edge case, then minimal date is in the past, if page stays open long enough
const TODAY = moment().toDate();
const MIN_START_TIME = moment().set({ hours: 0, minutes: 0 }).toDate();
const MAX_START_TIME = moment().set({ hours: 23, minutes: 0 }).toDate();
const MAX_END_TIME = moment().set({ hours: 23, minutes: 30 }).toDate();

const Timeslot = (props) => {
  const { FormInput, name, timeslot, setValue, forcePastDate } = props;
  const { date, startTime, endTime } = timeslot;
  const errorName = props.errorName ?? name;

  let minDate = TODAY;
  let maxDate = null;
  if (forcePastDate) {
    minDate = null;
    maxDate = TODAY;
  }
  const maxTime = useMemo(() => (isSameDay(date, maxDate) ? maxDate : MAX_END_TIME), [
    date,
    maxDate,
  ]);
  const minTime = useMemo(() => (isSameDay(date, minDate) ? minDate : MIN_START_TIME), [
    date,
    minDate,
  ]);

  // -30 so we can pick at least 1 end time option
  let maxStartTime = addMinutes(maxTime, -30);
  if (maxStartTime > MAX_START_TIME) maxStartTime = MAX_START_TIME;

  useResetEndTimeIfBeforeStartTime(setValue, name, startTime, endTime);

  useResetTimeIfOutOfRange({
    setValue,
    name,
    date,
    startTime,
    endTime,
    maxTime,
    minTime,
  });

  return (
    <div className={classnames(styles.rowWrapper, styles.threeElements)}>
      <FormInput
        type='simple-datepicker'
        name={`${name}.date`}
        nameForError={formatSubfield(errorName, 'startAt')}
        label={t`Date`}
        minDate={minDate}
        maxDate={maxDate}
        required
      />

      <div className={styles.timeInput}>
        <FormInput
          name={`${name}.startTime`}
          label={t`Start Time`}
          nameForError={formatSubfield(errorName, 'startAt')}
          minTime={minTime}
          maxTime={maxStartTime}
          {...TIME_INPUT_PROPS}
          required
        />
      </div>

      <div className={styles.timeInput}>
        <FormInput
          name={`${name}.endTime`}
          label={t`End Time`}
          disabled={!startTime}
          minTime={addMinutes(startTime, 30)}
          maxTime={maxTime}
          nameForError={formatSubfield(errorName, 'endAt')}
          {...TIME_INPUT_PROPS}
          required
        />
      </div>
    </div>
  );
};

Timeslot.propTypes = {
  timeslot: PropTypes.shape({
    endTime: PropTypes.instanceOf(Date),
    startTime: PropTypes.instanceOf(Date),
    date: PropTypes.instanceOf(Date),
  }),
  FormInput: PropTypes.func.isRequired,
  setValue: PropTypes.func.isRequired,
  index: PropTypes.number,
  name: PropTypes.string.isRequired,
  errorName: PropTypes.string,
  forcePastDate: PropTypes.bool,
};

Timeslot.defaultProps = {
  index: 0,
  timeslot: {},
  startTime: null,
  errorName: '',
  forcePastDate: false,
};

const addMinutes = (date, minutes) =>
  date != null ? moment(date).add(minutes, 'minutes').toDate() : null;

const isSameDay = (date, otherDate) =>
  date && otherDate && moment(date).isSame(moment(otherDate), 'day');

function useResetEndTimeIfBeforeStartTime(setValue, name, startTime, endTime) {
  useEffect(() => {
    const isEndBeforeStart = moment(endTime).isBefore(moment(startTime));
    if (!isEndBeforeStart) return;

    setValue(`${name}.endTime`, null);
  }, [startTime, endTime, name, setValue]);
}

function useResetTimeIfOutOfRange(state) {
  const { setValue, name, date, startTime, endTime, minTime, maxTime } = state;

  const prevDate = usePrevious(date);

  useEffect(() => {
    const shouldReset =
      !isSameDay(date, prevDate) &&
      isTimeOutOfRange(startTime, endTime, minTime, maxTime);
    if (!shouldReset) return;

    setValue(`${name}.startTime`, null);
    setValue(`${name}.endTime`, null);
  }, [date, name, prevDate, startTime, endTime, setValue, minTime, maxTime]);
}

const isTimeOutOfRange = (startTime, endTime, minTime, maxTime) =>
  (minTime && startTime && isBeforeHour(startTime, minTime)) ||
  (maxTime && endTime && isAfterHour(endTime, maxTime));

const isAfterHour = (time, maxTime) => moment(time).isAfter(moment(maxTime), 'hour');
const isBeforeHour = (time, minTime) => moment(time).isBefore(moment(minTime), 'hour');

export default Timeslot;
