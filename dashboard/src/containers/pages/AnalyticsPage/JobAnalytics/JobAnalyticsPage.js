import React, { useState } from 'react';
import { Row, Col, BreadcrumbItem } from 'reactstrap';
import { connect } from 'react-redux';
import { MdChevronRight } from 'react-icons/md';
import { Link } from 'react-router-dom';

import moment from 'moment';
import _ from 'lodash';
import { Trans, t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import { useSwagger } from '@hooks';
import { DefaultPageContainer, ReqStatus } from '@components';

import AnalyticsParams from '../AnalyticsParams';
import CandidatesStatuses from './CandidatesStatuses';
import CurrentCandidatesFunnel from './CurrentCandidatesFunnel';
import SnapshotTableModal from './SnapshotTableModal';

const mapStateToProps = (state) => ({
  shortlistStatuses: state.settings.localeData.proposalShortlistStatuses,
  longlistStatuses: state.settings.localeData.proposalLonglistStatuses,
});

function JobAnalyticsBreadcrumb(props) {
  const { jobTitle } = props;
  return (
    <>
      <BreadcrumbItem className='d-flex align-items-center'>
        <Link to='/c/jobs'>
          <Trans>Jobs</Trans>
        </Link>
        <MdChevronRight size='1.5em' />
      </BreadcrumbItem>
      <BreadcrumbItem active>
        <Trans>{jobTitle} Analytics</Trans>
      </BreadcrumbItem>
    </>
  );
}

function JobAnalyticsPage(props) {
  const { jobId } = props.match.params;
  const { shortlistStatuses, longlistStatuses } = props;

  const { obj: job, loading, errorObj: error } = useSwagger('jobs_read', { id: jobId });

  const [snapshotModal, setSnapshotModal] = useState(false);
  const [funnelData, setFunnelData] = useState(null);

  const [params, setParams] = useState({
    granularity: 'day',
    dateStart: moment().subtract(1, 'months').toDate(),
    dateEnd: moment().toDate(),
    job: jobId,
    status__in: null,
  });

  if (!job || error) {
    return <ReqStatus {...{ loading, error }} />;
  }

  const toggleSnapshot = () => setSnapshotModal(!snapshotModal);

  const mapStatusToGroup = (statuses) => {
    return _.map(statuses, (status) => status.group);
  };

  const mapStatusGroupToId = (groups) => {
    const proposalStatuses = _.concat(shortlistStatuses, longlistStatuses);

    return _.map(
      _.filter(proposalStatuses, (s) => _.includes(groups, s.group)),
      (s) => s.id
    );
  };

  const openSnapshot = ({ date, rate }) => {
    let statuses = [];
    switch (rate) {
      case 'identified':
        break;
      case 'contacted':
        statuses = mapStatusGroupToId(
          _.without(
            mapStatusToGroup(_.concat(shortlistStatuses, longlistStatuses)),
            'not_contacted'
          )
        );
        break;
      case 'interviewed':
        statuses = mapStatusGroupToId(['interviewed_internally']);
        break;
      case 'shortlisted':
        statuses = mapStatusGroupToId(mapStatusToGroup(shortlistStatuses));
        break;
      default:
        break;
    }
    setParams({ ...params, date, status__in: statuses });
    toggleSnapshot();
  };

  const onSnapshotClosed = () => {
    // clean snapshot
    setParams({
      ...params,
      date: null,
      status__in: null,
    });
  };

  return (
    <DefaultPageContainer
      title={props.i18n._(t`${job.title} Analytics`)}
      breadcrumb={<JobAnalyticsBreadcrumb jobTitle={job.title} />}
    >
      <Row>
        <Col className='d-flex'>
          <div className='ml-auto d-flex align-items-center'>
            <AnalyticsParams
              params={params}
              setParams={setParams}
              granularities={['day', 'week', 'month']}
            />
          </div>
        </Col>
      </Row>
      <Row className='mb-32'>
        <CandidatesStatuses
          openSnapshot={openSnapshot}
          setFunnelData={setFunnelData}
          params={params}
        />
      </Row>
      <Row>
        <CurrentCandidatesFunnel
          data={funnelData}
          openSnapshot={openSnapshot}
          params={params}
        />
      </Row>
      <SnapshotTableModal
        isOpen={snapshotModal}
        toggle={toggleSnapshot}
        onClosed={onSnapshotClosed}
        job={job}
        params={params}
      />
    </DefaultPageContainer>
  );
}

export default connect(mapStateToProps)(withI18n()(JobAnalyticsPage));
