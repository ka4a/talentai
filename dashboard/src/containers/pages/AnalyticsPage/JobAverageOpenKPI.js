import React from 'react';

import { useLingui } from '@lingui/react';
import { t } from '@lingui/macro';

import { Loading } from '@components/UI/Loading';

import AnalyticsBlock from './AnalyticsBlock';
import { useSwagger } from '../../../hooks';
import ErrorPlaceholder from './ErrorPlaceholder';
import NoDataPlaceholder from './NoDataPlaceholder';

export default function JobAverageOpenKPI({ dateStart, dateEnd }) {
  const { obj: data, loading, error } = useSwagger('stats_job_average_open_kpi', {
    date_start: dateStart,
    date_end: dateEnd,
  });
  const { i18n } = useLingui();

  return (
    <AnalyticsBlock
      title={i18n._(t`Avg. Days Open Per Job`)}
      titleSizeSm
      size={3}
      height='120px'
    >
      {loading && <Loading />}
      {!loading && error && <ErrorPlaceholder />}
      {data && !loading && (
        <>
          {data.value ? (
            <span className='fs-24 font-weight-bold'>{data.value.toFixed(0)}</span>
          ) : (
            <NoDataPlaceholder />
          )}
        </>
      )}
    </AnalyticsBlock>
  );
}
