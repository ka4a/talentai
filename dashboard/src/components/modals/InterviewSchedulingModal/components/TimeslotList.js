import React, { useCallback, useMemo } from 'react';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { DynamicList } from '@components';

import Timeslot from './Timeslot';

const TimeslotList = (props) => {
  const {
    data,
    FormInput,
    addFieldRow,
    removeFieldRow,
    setValue,
    name,
    errorName,
  } = props;

  const onAddRow = useCallback(() => {
    addFieldRow({
      key: name,
      defaultObject: { date: null, startTime: null, endTime: null },
    });
  }, [addFieldRow, name]);

  const onRemoveRow = useCallback(
    (event) => {
      removeFieldRow(event, name);
    },
    [removeFieldRow, name]
  );

  const fields = useMemo(
    () => [
      {
        id: 1,
        render: (index, timeslot) => (
          <Timeslot
            timeslot={timeslot}
            setValue={setValue}
            FormInput={FormInput}
            name={`${name}[${index}]`}
            errorName={typeof errorName === 'function' ? errorName(index) : errorName}
          />
        ),
      },
    ],
    [FormInput, setValue, name, errorName]
  );

  return (
    <DynamicList
      data={data}
      fields={fields}
      onAddRow={onAddRow}
      onRemoveRow={onRemoveRow}
      addRowText={t`+ Add Time Slot`}
    />
  );
};

TimeslotList.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      date: PropTypes.string,
      startAt: PropTypes.string,
      endAt: PropTypes.string,
    })
  ).isRequired,
  name: PropTypes.string,
  errorName: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  setValue: PropTypes.func.isRequired,
  FormInput: PropTypes.func.isRequired,
  addFieldRow: PropTypes.func.isRequired,
  removeFieldRow: PropTypes.func.isRequired,
};

TimeslotList.defaultProps = {
  name: 'sourceTimeslots',
};

export default TimeslotList;
