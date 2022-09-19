import React, { useState } from 'react';
import { FiCircle } from 'react-icons/fi';

import moment from 'moment';
import _ from 'lodash';
import {
  CartesianGrid,
  Line,
  LineChart,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Dot,
} from 'recharts';
import { Trans } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import { Loading } from '@components/UI/Loading';

import { useSwagger } from '../../../../hooks';
import AnalyticsBlock from '../AnalyticsBlock';
import NoDataPlaceholder from '../NoDataPlaceholder';
import ErrorPlaceholder from '../ErrorPlaceholder';
import { CHART_LABELS, CHART_COLORS } from './consts';

const dayTickFormatter = (d) => moment(d).format('MM.DD');
const weekTickFormatter = (d) => moment(d).format("DD MMM 'YY");
const monthTickFormatter = (d) => moment(d).format("MMM 'YY");

const QUERY_DATE_FORMAT = 'YYYY-MM-DD';

const dataLines = ['identified', 'contacted', 'interviewed', 'shortlisted'];

function CandidatesStatuses(props) {
  const { i18n, openSnapshot, params, setFunnelData } = props;

  const initialState = {
    identified: {
      active: true,
      color: CHART_COLORS.identified,
      name: i18n._(CHART_LABELS.identified),
    },
    contacted: {
      active: true,
      color: CHART_COLORS.contacted,
      name: i18n._(CHART_LABELS.contacted),
    },
    interviewed: {
      active: true,
      color: CHART_COLORS.interviewed,
      name: i18n._(CHART_LABELS.interviewed),
    },
    shortlisted: {
      active: true,
      color: CHART_COLORS.shortlisted,
      name: i18n._(CHART_LABELS.shortlisted),
    },
  };
  const title = <Trans>Candidates</Trans>;

  const requestParams = {
    granularity: params.granularity,
    job: params.job,
    date_start: moment(params.dateStart).format(QUERY_DATE_FORMAT),
    date_end: moment(params.dateEnd).format(QUERY_DATE_FORMAT),
  };

  const { obj: data, loading, error } = useSwagger('stats_candidates_statuses', {
    ...requestParams,
  });

  const [state, setState] = useState(initialState);

  if (loading) {
    return (
      <AnalyticsBlock title={title}>
        <Loading />
      </AnalyticsBlock>
    );
  } else if (error) {
    return (
      <AnalyticsBlock title={title}>
        <ErrorPlaceholder />
      </AnalyticsBlock>
    );
  } else if (_.every(data, (i) => i.value === 0.0)) {
    return (
      <AnalyticsBlock title={title}>
        <NoDataPlaceholder />
      </AnalyticsBlock>
    );
  }

  setFunnelData(_.last(data.lineData));

  const toggleLine = (line) => {
    const lineState = state[line];
    setState({
      ...state,
      [line]: {
        ...lineState,
        active: !lineState.active,
      },
    });
  };

  const getTickFormatter = () => {
    switch (params.granularity) {
      case 'week':
        return weekTickFormatter;
      case 'month':
        return monthTickFormatter;
      default:
        return dayTickFormatter;
    }
  };

  const formatTooltip = (value, line, props) => {
    const { payload } = props;
    const diffs = _.find(data.diffs, (entry) => entry.date === payload.date);

    const name = state[line].name;
    const diff = `${value} (+${diffs[line]})`;

    return [diff, name];
  };

  const renderLegend = (props) => {
    return (
      <div className='d-flex flex-column pl-24'>
        {_.map(dataLines, (dataLine, i) => {
          const line = state[dataLine];
          const iconProps = {
            fill: line.active ? line.color : '#F6F9FC',
          };

          return (
            <span
              className='d-flex align-items-center cursor-pointer'
              key={`legend-item-${i}`}
              onClick={() => toggleLine(dataLine)}
            >
              <FiCircle color={line.color} className='mr-4' {...iconProps} />
              <span>{line.name}</span>
            </span>
          );
        })}
      </div>
    );
  };

  const onChartClick = (payload) => {
    const date = _.get(payload, 'activeLabel');

    if (date) openSnapshot({ date });
  };

  const onDotClick = ({ dataKey, payload: { date } }, event) => {
    event.stopPropagation();
    openSnapshot({ date, rate: dataKey });
  };

  const getLine = (line) => {
    const { active, color } = state[line];
    return active ? (
      <Line
        key={line}
        type='monotone'
        dataKey={line}
        stroke={color}
        strokeWidth={5}
        dot={{ fill: color, r: 5, strokeWidth: 0 }}
        activeDot={<Dot r={9} onClick={onDotClick} />}
      />
    ) : null;
  };

  return (
    <AnalyticsBlock
      title={title}
      size={12}
      chartContainerStyles={{ overflowY: 'hidden' }}
    >
      {data && (
        <ResponsiveContainer>
          <LineChart
            data={data.lineData}
            margin={{ bottom: 24, top: 24 }}
            onClick={onChartClick}
          >
            <CartesianGrid vertical={false} strokeDasharray='7 7' />
            <XAxis
              angle={requestParams.granularity === 'week' ? 30 : undefined}
              dy={16}
              dataKey='date'
              stroke='#8593A3'
              tickFormatter={getTickFormatter()}
            />
            <YAxis allowDecimals={false} stroke='#8593A3' />
            <Tooltip labelFormatter={getTickFormatter()} formatter={formatTooltip} />
            {_.map(dataLines, getLine)}
            <Legend
              align='right'
              layout='vertical'
              iconType='circle'
              verticalAlign='middle'
              content={renderLegend}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </AnalyticsBlock>
  );
}

export default withI18n()(CandidatesStatuses);
