import React from 'react';

import classnames from 'classnames';
import { Line, LineChart, ResponsiveContainer } from 'recharts';

import { Loading } from '@components/UI/Loading';

import AnalyticsBlock from './AnalyticsBlock';
import { useSwagger } from '../../../hooks';
import ErrorPlaceholder from './ErrorPlaceholder';

function renderMonthDiff(data) {
  const prev = data[data.length - 2].value;
  const curr = data[data.length - 1].value;

  if (prev < 1) {
    return <div>{''}</div>;
  }

  const val = -(1.0 - curr / prev);

  return (
    <span
      className={classnames({ 'text-danger': val < 0 }, { 'text-success': val > 0 })}
    >
      {`${val > 0 ? '+' : ''}${(val * 100).toFixed(0)}%`}
    </span>
  );
}

export default function BlockKPI({ title, operationId, dateStart, dateEnd }) {
  const { obj: data, loading, error } = useSwagger(operationId, {
    filter_type: 'team', // TODO: add 'total' / make not required?
    filter_value: null,
    date_start: dateStart,
    date_end: dateEnd,
    granularity: 'month',
  });

  return (
    <AnalyticsBlock title={title} titleSizeSm size={3} height='120px'>
      {loading && <Loading />}
      {!loading && error && <ErrorPlaceholder />}
      {data && !loading && (
        <div className='d-flex'>
          <div>
            <div className='d-inline fs-24 font-weight-bold'>
              {data[data.length - 1].value}
            </div>
            <div className='d-inline fs-14 font-weight-bold ml-8 align-text-bottom'>
              {renderMonthDiff(data)}
            </div>
          </div>
          <div className='ml-auto' style={{ width: '80px', height: '1.5rem' }}>
            <ResponsiveContainer>
              <LineChart width={300} height={100} data={data}>
                <Line
                  type='monotone'
                  dataKey='value'
                  dot={false}
                  stroke='#4781F7'
                  strokeWidth={3}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </AnalyticsBlock>
  );
}
