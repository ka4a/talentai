import React from 'react';

import _ from 'lodash';
import { Funnel, FunnelChart, LabelList, ResponsiveContainer, Tooltip } from 'recharts';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { getChoiceName } from '@utils';
import { Loading } from '@components/UI/Loading';
import { PROPOSAL_STATUS_GROUP_CHOICES } from '@constants';

import AnalyticsBlock from './AnalyticsBlock';
import NoDataPlaceholder from './NoDataPlaceholder';
import ErrorPlaceholder from './ErrorPlaceholder';
import { useSwagger, useTranslatedChoices } from '../../../hooks';

const COLORS = ['#8884d8', '#83a6ed', '#8dd1e1', '#82ca9d', '#a4de6c'];

function ConversionRatioFunnel(props) {
  const { filterType, filterValue, dateStart, dateEnd, i18n } = props;

  const proposalStatusGroupChoices = useTranslatedChoices(
    i18n,
    PROPOSAL_STATUS_GROUP_CHOICES
  );

  const { obj: data, loading, error } = useSwagger(
    'stats_conversion_ratio',
    {
      filter_type: filterType,
      filter_value: filterValue,
      date_start: dateStart,
      date_end: dateEnd,
    },
    (data) => {
      _.each(data, (el, i) => (el.fill = COLORS[i % COLORS.length]));

      data.completionRate = 0;
      if (data[0].value > 0) {
        data.completionRate = (data[data.length - 1].value / data[0].value) * 100.0;
      }

      return data;
    }
  );

  const hasData = !loading && _.some(data, (i) => i.value !== 0.0);

  return (
    <AnalyticsBlock
      title={i18n._(t`Candidate Conversion Ratio`)}
      childrenAboveChart={
        <>
          {data && !loading && hasData && (
            <div>
              <span className='text-muted'>
                <Trans>
                  Funnel Completion Rate:<span>&nbsp;</span>
                </Trans>
              </span>
              <span className='fs-24 font-weight-bold'>
                {data.completionRate.toFixed(0)}%
              </span>
            </div>
          )}
        </>
      }
    >
      {loading && <Loading />}
      {!loading && error && <ErrorPlaceholder />}
      {!loading && data && !hasData && <NoDataPlaceholder />}
      {!loading && data && hasData && (
        <ResponsiveContainer>
          <FunnelChart margin={{ right: 16, left: 8, bottom: 16 }}>
            <Tooltip />
            <Funnel dataKey='value' data={data} isAnimationActive>
              <LabelList
                position='right'
                fill='#000'
                stroke='none'
                dataKey='statusGroup'
                formatter={(value) => getChoiceName(proposalStatusGroupChoices, value)}
              />
            </Funnel>
          </FunnelChart>
        </ResponsiveContainer>
      )}
    </AnalyticsBlock>
  );
}

export default withI18n()(ConversionRatioFunnel);
