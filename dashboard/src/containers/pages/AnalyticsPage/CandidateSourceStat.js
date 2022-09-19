import React, { useState } from 'react';

import _ from 'lodash';
import { Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { Loading } from '@components/UI/Loading';

import AnalyticsBlock from './AnalyticsBlock';
import PieChartCustomLabel from './PieChartCustomLabel';
import NoDataPlaceholder from './NoDataPlaceholder';
import { useSwagger } from '../../../hooks';
import FilterButton from './FilterButton';
import ErrorPlaceholder from './ErrorPlaceholder';

const COLORS = ['#8884d8', '#4781F7', '#74A5FA', '#82ca9d'];

function CandidateSourceStat(props) {
  const { filterType, filterValue, filterValueName, dateStart, dateEnd, i18n } = props;

  const [hiredFilter, setHiredFilter] = useState(false);

  const { obj: data, loading, error } = useSwagger(
    'stats_sources',
    {
      filter_type: filterType,
      filter_value: filterValue,
      date_start: dateStart,
      date_end: dateEnd,
      hired: hiredFilter,
    },
    (data) => {
      _.each(data, (el, i) => (el.fill = COLORS[i % COLORS.length]));
      return data;
    }
  );

  let helpText = [i18n._(t`Hired Candidates source`)];

  if (filterType === 'team') {
    helpText.push(filterValue === null ? '' : i18n._(t`by department`));
  } else if (filterType === 'hiring_manager') {
    helpText.push(filterValue === null ? '' : i18n._(t`by hiring manager`));
  } else if (filterType === 'function') {
    helpText.push(filterValue === null ? '' : i18n._(t`in function`));
  }

  if (filterValue !== null) {
    helpText.push(`"${filterValueName}"`);
  }

  helpText = helpText.join(' ');

  return (
    <AnalyticsBlock
      title={i18n._(t`Source of Candidates`)}
      helpText={helpText}
      childrenAboveChart={
        <div>
          <FilterButton
            className='d-inline-block'
            selected={!hiredFilter}
            onClick={() => setHiredFilter(false)}
          >
            <Trans>All</Trans>
          </FilterButton>
          <FilterButton
            className='d-inline-block ml-8'
            selected={hiredFilter}
            onClick={() => setHiredFilter(true)}
          >
            <Trans>Hired</Trans>
          </FilterButton>
        </div>
      }
    >
      {loading && <Loading />}
      {!loading && error && <ErrorPlaceholder />}
      {!loading && data && !data.length && <NoDataPlaceholder />}
      {!loading && data && data.length > 0 && (
        <ResponsiveContainer>
          <PieChart margin={{ top: 20, right: 20, left: 20, bottom: 20 }}>
            <Pie
              dataKey='value'
              isAnimationActive={false}
              data={data}
              labelLine={false}
              label={PieChartCustomLabel}
              outerRadius={80}
              fill='#8884d8'
            />
            <Tooltip />
            <Legend
              iconSize={10}
              iconType='circle'
              width={120}
              height={140}
              layout='vertical'
              verticalAlign='middle'
              align='right'
            />
          </PieChart>
        </ResponsiveContainer>
      )}
    </AnalyticsBlock>
  );
}

export default withI18n()(CandidateSourceStat);
