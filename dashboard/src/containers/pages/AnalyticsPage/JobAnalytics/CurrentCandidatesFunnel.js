import React from 'react';

import moment from 'moment';
import _ from 'lodash';
import { Funnel, FunnelChart, Tooltip, LabelList, ResponsiveContainer } from 'recharts';
import { Trans } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import AnalyticsBlock from '../AnalyticsBlock';
import NoDataPlaceholder from '../NoDataPlaceholder';
import { CHART_COLORS, CHART_LABELS } from './consts';

const QUERY_DATE_FORMAT = 'YYYY-MM-DD';

function CurrentCandidatesFunnel(props) {
  const { i18n, data, openSnapshot, params } = props;

  const title = <Trans>Candidates shortlisting funnel</Trans>;
  if (!data) {
    return (
      <AnalyticsBlock title={title}>
        <NoDataPlaceholder />
      </AnalyticsBlock>
    );
  }

  const funnelSchema = [
    {
      key: 'identified',
      name: i18n._(CHART_LABELS.identified),
      fill: CHART_COLORS.identified,
    },
    {
      key: 'contacted',
      name: i18n._(CHART_LABELS.contacted),
      fill: CHART_COLORS.contacted,
    },
    {
      key: 'interviewed',
      name: i18n._(CHART_LABELS.interviewed),
      fill: CHART_COLORS.interviewed,
    },
    {
      key: 'shortlisted',
      name: i18n._(CHART_LABELS.shortlisted),
      fill: CHART_COLORS.shortlisted,
    },
  ];

  const onChartClick = ({ payload }) => {
    const key = _.get(payload, 'key');

    if (!key) return;

    const date = moment(params.dateEnd).format(QUERY_DATE_FORMAT);
    openSnapshot({ date, rate: key });
  };

  const funnelData = _.map(funnelSchema, (fs) => ({ value: data[fs.key], ...fs }));

  return (
    <AnalyticsBlock title={title}>
      <ResponsiveContainer>
        <FunnelChart margin={{ right: 16, left: 8, bottom: 16 }}>
          <Funnel
            dataKey='value'
            data={funnelData}
            isAnimationActive
            onClick={onChartClick}
          >
            <LabelList position='right' fill='#000' stroke='none' dataKey='name' />
          </Funnel>
          <Tooltip />
        </FunnelChart>
      </ResponsiveContainer>
    </AnalyticsBlock>
  );
}

export default withI18n()(CurrentCandidatesFunnel);
