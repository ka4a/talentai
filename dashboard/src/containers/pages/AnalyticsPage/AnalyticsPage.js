import React from 'react';
import { Col, Row } from 'reactstrap';
import { connect } from 'react-redux';
import { Container } from 'reactstrap';

import _ from 'lodash';
import moment from 'moment';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { DefaultPageContainer, SelectInput } from '@components';
import { fetchLoadingWrapper } from '@components/ReqStatus';
import { client } from '@client';

import JobAverageOpen from './JobAverageOpen';
import CandidateSourceStat from './CandidateSourceStat';
import ContractedAgenciesKPI from './ContractedAgenciesKPI';
import OpenJobs from './OpenJobs';
import CandidatesHired from './CandidatesHired';
import CandidateDeclineReasonStat from './CandidateDeclineReasonStat';
import OpenJobsKPI from './OpenJobsKPI';
import JobAverageOpenKPI from './JobAverageOpenKPI';
import CandidatesHiredKPI from './CandidatesHiredKPI';
import ConversionRatioFunnel from './ConversionRatioFunnel';
import CandidatesByStage from './CandidatesByStage';
import AnalyticsParams from './AnalyticsParams';

const mapStateToProps = (state) => ({
  locale: state.settings.locale,
});

const FILTER_BY = [
  { value: 'team', label: t`Department` },
  { value: 'function', label: t`Function` },
  { value: 'owner', label: t`Job Owner` },
];

const QUERY_DATE_FORMAT = 'YYYY-MM-DD';

const STATE_FILTER_OPTION_FIELDS = {
  team: 'teams',
  owner: 'staff',
  function: 'function',
};

class AnalyticsPage extends React.PureComponent {
  state = {
    function: null,
    teams: null,
    hiringManagers: null,

    dateStartKPI: moment()
      .subtract(6, 'months')
      .startOf('month')
      .format(QUERY_DATE_FORMAT),
    dateEndKPI: moment().add(1, 'days').format(QUERY_DATE_FORMAT),

    dateStart: moment().subtract(2, 'months').toDate(),
    dateEnd: moment().toDate(),
    granularity: 'month',

    filterType: 'team',
    filterValue: null,
  };

  fetchData = fetchLoadingWrapper(() => [
    client
      .execute({
        operationId: 'function_list',
      })
      .then((response) => {
        this.setState({
          function: _.map(response.obj, (obj) => ({
            value: obj.id,
            name: obj.title,
          })),
        });
      }),
    client
      .execute({
        operationId: 'team_list',
      })
      .then((response) => {
        this.setState({
          teams: _.map(response.obj, (obj) => ({ value: obj.id, name: obj.name })),
        });
      }),
    client
      .execute({
        operationId: 'staff_list',
        parameters: { count: 1000 },
      })
      .then((response) => {
        this.setState({
          staff: _.map(response.obj.results, (obj) => ({
            value: obj.id,
            name: `${obj.firstName} ${obj.lastName}`,
          })),
        });
      }),
  ]).bind(this);

  componentDidMount() {
    this.fetchData();
  }

  setFilterType = (value) => {
    this.setState({ filterType: value, filterValue: null });
  };

  setFilterValue = (value) => {
    this.setState({ filterValue: value });
  };

  getTranslatedLabel = (option) => this.props.i18n._(option.label);

  render() {
    const {
      filterType,
      filterValue,
      dateStart,
      dateEnd,
      granularity,
      dateStartKPI,
      dateEndKPI,
    } = this.state;

    const currentFilterOptions = this.state[STATE_FILTER_OPTION_FIELDS[filterType]];

    const filterValueObj = _.find(currentFilterOptions, { value: filterValue });
    const filterValueName = filterValueObj ? filterValueObj.name : null;

    const blockKPIAttrs = {
      dateStart: dateStartKPI,
      dateEnd: dateEndKPI,
    };

    const blockAttrs = {
      filterType,
      filterValue,
      filterValueName,
      dateStart: moment(dateStart).format(QUERY_DATE_FORMAT),
      dateEnd: moment(dateEnd).add(1, 'days').format(QUERY_DATE_FORMAT),
      granularity,
    };

    return (
      <DefaultPageContainer title={this.props.i18n._(t`Analytics`)}>
        <Container>
          <Row>
            <OpenJobsKPI {...blockKPIAttrs} />
            <CandidatesHiredKPI {...blockKPIAttrs} />
            <JobAverageOpenKPI {...blockKPIAttrs} />
            <ContractedAgenciesKPI {...blockKPIAttrs} />
          </Row>

          <Row className='mt-48 mb-32'>
            <Col className='d-flex'>
              <div>
                <h2>
                  <Trans>Analytics</Trans>
                </h2>
              </div>
              <div className='ml-auto d-flex align-items-center'>
                <SelectInput
                  className='d-inline-block mx-8'
                  size='sm'
                  options={FILTER_BY}
                  getLabel={this.getTranslatedLabel}
                  value={filterType}
                  onSelect={this.setFilterType}
                />
                <SelectInput
                  className='d-inline-block mx-8'
                  options={[
                    { value: null, label: <Trans>All</Trans> },
                    ...(currentFilterOptions ? currentFilterOptions : []),
                  ]}
                  value={filterValue}
                  onSelect={this.setFilterValue}
                />
                <AnalyticsParams
                  params={this.state}
                  setParams={this.setState.bind(this)}
                  granularities={['week', 'month']}
                />
              </div>
            </Col>
          </Row>

          <Row>
            <OpenJobs {...blockAttrs} />
            <JobAverageOpen {...blockAttrs} />
            <CandidatesByStage {...blockAttrs} />
            <CandidateSourceStat {...blockAttrs} />
            <ConversionRatioFunnel {...blockAttrs} />
            <CandidatesHired {...blockAttrs} />
            <CandidateDeclineReasonStat {...blockAttrs} />
          </Row>
        </Container>
      </DefaultPageContainer>
    );
  }
}

export default connect(mapStateToProps)(withI18n()(AnalyticsPage));
