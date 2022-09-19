import React, { useEffect, useState } from 'react';

import moment from 'moment';
import PropTypes from 'prop-types';

const WEEK = 1000 * 60 * 60 * 24 * 7;

const getDateDisplay = (momentDate, threshold) =>
  moment().diff(momentDate) < threshold
    ? momentDate.fromNow()
    : momentDate.format('LLL');

const HumanizedDate = ({ date = '', threshold = WEEK }) => {
  // eslint-disable-next-line no-unused-vars
  const [currentTime, setCurrentTime] = useState(() => moment());

  // for force rerendering date (a few seconds ago, a minute ago, ...)
  useEffect(() => {
    let intervalId = null;

    if (date) {
      // don't start if date is empty
      intervalId = setInterval(() => {
        setCurrentTime(moment());
      }, 1000 * 10);
    }

    return () => {
      if (intervalId !== null) {
        clearInterval(intervalId);
      }
    };
  }, [date]);

  const momentDate = moment(date);
  return (
    <span title={date}>
      {momentDate.isValid() ? getDateDisplay(momentDate, threshold) : ''}
    </span>
  );
};

HumanizedDate.propTypes = {
  date: PropTypes.string,
};

export default HumanizedDate;
