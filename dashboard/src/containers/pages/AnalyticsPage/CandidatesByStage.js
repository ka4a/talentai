import React, { useState } from 'react';

import _ from 'lodash';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { getChoiceName } from '@utils';
import { Loading } from '@components/UI/Loading';
import { PIPELINE_ITEMS_CHOICES } from '@constants';

import ProposalsPipeline from '../../../components/jobs/ProposalsPipeline';
import AnalyticsBlock from './AnalyticsBlock';
import { useSwagger, useTranslatedChoices } from '../../../hooks';
import SelectInput from '../../../components/SelectInput';
import NoDataPlaceholder from './NoDataPlaceholder';
import ErrorPlaceholder from './ErrorPlaceholder';

function CandidatesByStage(props) {
  const { filterType, filterValue, filterValueName, dateStart, dateEnd, i18n } = props;

  const [sortByField, setSortByField] = useState('received');

  const pipelineItemsChoices = useTranslatedChoices(i18n, PIPELINE_ITEMS_CHOICES);

  const { obj: unsortedData, loading, error } = useSwagger(
    'stats_proposal_status_count',
    {
      filter_type: filterType,
      filter_value: filterValue,
      date_start: dateStart,
      date_end: dateEnd,
    }
  );

  let helpText = [i18n._(t`Candidates by stage`)];

  if (filterType === 'team') {
    helpText.push(filterValue === null ? '' : i18n._(t`for department`));
  } else if (filterType === 'hiring_manager') {
    helpText.push(filterValue === null ? '' : i18n._(t`for hiring manager`));
  } else if (filterType === 'function') {
    helpText.push(filterValue === null ? '' : i18n._(t`in function`));
  }

  if (filterValue !== null) {
    helpText.push(`"${filterValueName}"`);
  }

  helpText = helpText.join(' ');

  const sortOptions =
    unsortedData && unsortedData.length > 0
      ? _.map(_.keys(unsortedData[0].proposalPipeline), (name) => ({
          value: name,
          label: getChoiceName(pipelineItemsChoices),
        }))
      : [];

  const data = unsortedData
    ? _.chain(unsortedData)
        .sortBy(({ proposalPipeline }) => proposalPipeline[sortByField])
        .reverse()
        .value()
    : [];

  return (
    <AnalyticsBlock
      title={i18n._(t`Candidates by Stage`)}
      helpText={helpText}
      childrenAboveChart={
        sortOptions.length > 0 && (
          <div className='mb-8'>
            <div className='d-inline-block text-muted font-weight-bold mr-8'>
              <Trans>Sort By</Trans>
            </div>
            <SelectInput
              className='d-inline-block'
              placeholder=''
              value={sortByField}
              triggerComponentProps={{ bsSize: '' }}
              onSelect={setSortByField}
              options={sortOptions}
            />
          </div>
        )
      }
    >
      {loading && <Loading />}
      {!loading && error && <ErrorPlaceholder />}
      {!loading && data && !data.length && <NoDataPlaceholder />}
      {!loading && data && data.length > 0 && (
        <div>
          {_.map(data, ({ name, proposalPipeline }, i) => (
            <div key={i}>
              <div className='font-weight-bold text-muted'>{name}</div>
              <ProposalsPipeline pipeline={proposalPipeline} valueColor='#374966' />
            </div>
          ))}
        </div>
      )}
    </AnalyticsBlock>
  );
}

export default withI18n()(CandidatesByStage);
