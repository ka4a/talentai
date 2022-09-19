import React from 'react';

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Loading } from '@components/UI/Loading';

import { useSwagger } from '../../../hooks';
import AnalyticsBlock from './AnalyticsBlock';
import NoDataPlaceholder from './NoDataPlaceholder';
import ErrorPlaceholder from './ErrorPlaceholder';

function JobAverageOpen(props) {
  const { filterType, filterValue, filterValueName, dateStart, dateEnd, i18n } = props;

  const { obj: data, loading, error } = useSwagger('stats_job_average_open', {
    filter_type: filterType,
    filter_value: filterValue,
    date_start: dateStart,
    date_end: dateEnd,
  });

  let helpText = [props.i18n._(t`Number of days a job was in progress`)];

  if (filterType === 'team') {
    helpText.push(
      filterValue === null ? i18n._(t`by departments`) : i18n._(t`for department`)
    );
  } else if (filterType === 'hiring_manager') {
    helpText.push(
      filterValue === null
        ? i18n._(t`by hiring managers`)
        : i18n._(t`for hiring manager`)
    );
  } else if (filterType === 'function') {
    helpText.push(
      filterValue === null ? i18n._(t`by function`) : i18n._(t`for function`)
    );
  }

  if (filterValue !== null) {
    helpText.push(`"${filterValueName}"`);
  }

  helpText = helpText.join(' ');

  return (
    <AnalyticsBlock title={i18n._(t`Job Average Days Open`)} helpText={helpText}>
      {loading && <Loading />}
      {!loading && error && <ErrorPlaceholder />}
      {!loading && data && !data.length && <NoDataPlaceholder />}
      {!loading && data && data.length > 0 && (
        <div
          style={{
            width: '100%',
            height: `${3 + data.length * 2}em`,
          }}
        >
          <ResponsiveContainer>
            <BarChart
              data={data}
              margin={{ top: 0, right: 0, left: 100, bottom: 0 }}
              layout='vertical'
              barSize={32}
            >
              <CartesianGrid vertical={false} strokeDasharray='7 7' />
              <YAxis
                type='category'
                dataKey='name'
                minTickGap={0}
                interval={0}
                axisLine={false}
                tickLine={false}
              />
              <XAxis type='number' axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar dataKey='openPeriodAvg' fill='#4781F7' />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </AnalyticsBlock>
  );
}

export default withI18n()(JobAverageOpen);
