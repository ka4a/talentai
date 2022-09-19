import React from 'react';
import DatePicker from 'react-datepicker';
import { connect } from 'react-redux';
import { Input } from 'reactstrap';

import _ from 'lodash';
import PropTypes from 'prop-types';
import moment from 'moment';
import { Trans } from '@lingui/macro';

import SelectInput from '../../../components/SelectInput';

const mapStateToProps = (state) => ({
  locale: state.settings.locale,
});

const GRANULARITY_OPTIONS = [
  { value: 'day', label: <Trans>Daily</Trans> },
  { value: 'week', label: <Trans>Weekly</Trans> },
  { value: 'month', label: <Trans>Monthly</Trans> },
];

function AnalyticsParams(props) {
  const { locale, params, setParams, granularities } = props;

  const granularityOptions = _.filter(GRANULARITY_OPTIONS, ({ value }) =>
    _.includes(granularities, value)
  );

  const updateGranularity = (granularity) => {
    setParams({ ...params, granularity });
  };

  const setDateStart = (dateStart) => {
    const updatedDates = { dateStart };
    if (dateStart > params.dateEnd) {
      updatedDates.dateEnd = dateStart;
    }
    setParams({ ...params, ...updatedDates });
  };

  const setDateEnd = (dateEnd) => {
    const updatedDates = { dateEnd };
    if (dateEnd < params.dateStart) {
      updatedDates.dateStart = dateEnd;
    }
    setParams({ ...params, ...updatedDates });
  };

  const { dateStart, dateEnd, granularity } = params;
  const maxDate = moment().toDate();

  return (
    <>
      <DatePicker
        selected={dateStart}
        selectsStart
        startDate={dateStart}
        endDate={dateEnd}
        dateFormat='yyyy/MM/dd'
        onChange={setDateStart}
        maxDate={maxDate}
        customInput={<Input className='w-auto mx-8' bsSize='lg' />}
        locale={locale}
      />
      <div className='mx-8'>{'~'}</div>
      <DatePicker
        selected={dateEnd}
        selectsEnd
        startDate={dateStart}
        endDate={dateEnd}
        dateFormat='yyyy/MM/dd'
        onChange={setDateEnd}
        maxDate={maxDate}
        customInput={<Input className='w-auto mx-8' bsSize='lg' />}
        locale={locale}
      />
      <SelectInput
        className='d-inline-block mx-8'
        options={granularityOptions}
        value={granularity}
        onSelect={updateGranularity}
      />
    </>
  );
}

AnalyticsParams.propTypes = {
  params: PropTypes.object.isRequired,
  setParams: PropTypes.func.isRequired,
  granularities: PropTypes.arrayOf(PropTypes.oneOf(['day', 'week', 'month']).isRequired)
    .isRequired,
};

export default connect(mapStateToProps)(AnalyticsParams);
