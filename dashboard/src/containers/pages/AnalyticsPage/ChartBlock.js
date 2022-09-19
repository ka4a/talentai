import React from 'react';

import moment from 'moment';
import classnames from 'classnames';
import _ from 'lodash';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Trans } from '@lingui/macro';

import { Loading } from '@components/UI/Loading';

import { useSwagger } from '../../../hooks';
import AnalyticsBlock from './AnalyticsBlock';
import NoDataPlaceholder from './NoDataPlaceholder';
import ErrorPlaceholder from './ErrorPlaceholder';

const monthTickFormatter = (d) => moment(d).format("MMM 'YY");
const weekTickFormatter = (d) => moment(d).format("DD MMM 'YY");

export default function ChartBlock(props) {
  const {
    title,
    helpText,
    operationId,
    filterType,
    filterValue,
    dateStart,
    dateEnd,
    granularity,
  } = props;

  const { obj: data, loading, error } = useSwagger(operationId, {
    filter_type: filterType,
    filter_value: filterValue,
    date_start: dateStart,
    date_end: dateEnd,
    granularity,
  });

  if (loading) {
    return (
      <AnalyticsBlock title={title} helpText={helpText}>
        <Loading />
      </AnalyticsBlock>
    );
  } else if (error) {
    return (
      <AnalyticsBlock title={title} helpText={helpText}>
        <ErrorPlaceholder />
      </AnalyticsBlock>
    );
  } else if (_.every(data, (i) => i.value === 0.0)) {
    return (
      <AnalyticsBlock title={title} helpText={helpText}>
        <NoDataPlaceholder />
      </AnalyticsBlock>
    );
  }

  let lastMonth;
  let prevMonth;
  let diff;

  if (data && data.length > 0) {
    lastMonth = data[data.length - 1].value;
    if (data.length > 1) {
      prevMonth = data[data.length - 2].value;
      diff = prevMonth > 0 ? lastMonth / prevMonth - 1.0 : 0;
    }
  }

  return (
    <AnalyticsBlock
      title={title}
      helpText={helpText}
      childrenAboveChart={
        data && !loading ? (
          <div className='d-flex mb-8'>
            {(lastMonth !== 0.0 || Boolean(diff)) && (
              <div className='mr-16'>
                <div className='text-muted'>
                  <Trans>Current Month</Trans>
                </div>
                <div className='fs-24 font-weight-bold'>{lastMonth}</div>
              </div>
            )}
            {Boolean(diff) && (
              <div>
                <div className='text-muted'>
                  <Trans>% Change from Previous Month</Trans>
                </div>
                <div className='fs-24 font-weight-bold'>
                  <span
                    className={classnames(
                      { 'text-success': diff > 0.0 },
                      { 'text-danger': diff < 0.0 }
                    )}
                  >
                    {(diff * 100.0).toFixed(0)}%
                  </span>
                </div>
              </div>
            )}
          </div>
        ) : null
      }
    >
      {data && (
        <ResponsiveContainer>
          <LineChart data={data} margin={{ bottom: 24 }}>
            <CartesianGrid vertical={false} strokeDasharray='7 7' />
            <XAxis
              type='category'
              dataKey='date'
              minTickGap={0}
              interval={0}
              angle={granularity === 'week' ? 30 : undefined}
              dy={16}
              axisLine={false}
              tickLine={false}
              stroke='#8593A3'
              tickFormatter={
                granularity === 'month' ? monthTickFormatter : weekTickFormatter
              }
            />
            <YAxis
              type='number'
              dataKey='value'
              axisLine={false}
              tickLine={false}
              stroke='#8593A3'
            />
            <Tooltip />
            <Line
              type='monotone'
              dataKey='value'
              stroke='#4781F7'
              strokeWidth={5}
              dot={{ fill: '#4781F7', r: 5, strokeWidth: 0 }}
              activeDot={{ r: 9 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </AnalyticsBlock>
  );
}
