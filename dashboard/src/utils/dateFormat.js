import moment from 'moment';

import { DATE_FORMAT, TIME_FORMAT } from '@constants';
import { getTimezoneOffset } from '@utils/common';

export const getFormattedDate = (date) => {
  return date ? moment(date).format(DATE_FORMAT.moment) : '';
};

export const formatTimeslot = (startAt, endAt, timeSeparator = '-') => {
  if (!(startAt && endAt)) return '';

  const date = moment(startAt).format(DATE_FORMAT.moment);
  const startHours = moment(startAt).format(TIME_FORMAT.moment);
  const endHours = moment(endAt).format(TIME_FORMAT.moment);

  return `${date}, ${startHours}${timeSeparator}${endHours}`;
};

export const formatSchedule = (startAt, endAt) => {
  const timeslot = formatTimeslot(startAt, endAt, ' - ');

  if (!timeslot) return null;

  const timezoneOffset = getTimezoneOffset();

  return `${timeslot} (GMT${timezoneOffset})`;
};
