import React, { memo, useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { Container } from 'reactstrap';

import classnames from 'classnames';
import { t, Trans } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import {
  Button,
  FormattedSalary,
  JobTitle,
  DefaultPageContainer,
  ProposalsPipeline,
  Typography,
  Badge,
  Table,
  TableHeader,
} from '@components';
import { useJobsList } from '@swrAPI';
import { getChoiceName } from '@utils';
import { useIsAuthenticatedByRoles, useTable, useTranslatedChoices } from '@hooks';
import {
  AGENCY_ADMINISTRATORS,
  AGENCY_MANAGERS,
  CLIENT_ADMINISTRATORS,
  CLIENT_INTERNAL_RECRUITERS,
  JOB_STATUS_BADGE_COLORS,
  JOB_STATUS_CHOICES,
  RECRUITERS,
} from '@constants';

import styles from './JobsPage.module.scss';

const USERS_ALLOWED_TO_CREATE_JOB = [
  CLIENT_ADMINISTRATORS,
  CLIENT_INTERNAL_RECRUITERS,
  AGENCY_ADMINISTRATORS,
  AGENCY_MANAGERS,
  RECRUITERS,
];

const STORE_TABLE_KEY = 'jobs';

const JobsPage = () => {
  const history = useHistory();

  const data = useTable({
    useGetData: useJobsList,
    storeKey: STORE_TABLE_KEY,
    paginationKey: 'jobsShowPer',
    params: {
      show_pipeline: true,
      is_belong_to_user_org: true,
    },
  });

  const { i18n } = useLingui();
  const jobStatusChoices = useTranslatedChoices(i18n, JOB_STATUS_CHOICES);

  const columns = [
    {
      sort: true,
      width: 295,
      text: t`Job Title`,
      dataField: 'title',
      formatter: (cell, job) => {
        return (
          <JobTitle
            className={classnames(`fs-16 d-flex`)}
            linkClassName={classnames(styles.jobTitle, 'text-capitalize text-medium')}
            job={job}
            link
            withTooltip
          />
        );
      },
    },
    {
      sort: true,
      width: 245,
      dataField: 'salaryTo',
      text: t`Annual Salary`,
      formatter: (cell, job) =>
        ['month', 'year'].includes(job.salaryPer) && (
          <Typography variant='caption' className={styles.caption}>
            <FormattedSalary job={job} hidePerName={true} isAnnual />
          </Typography>
        ),
    },
    {
      sort: true,
      width: 195,
      text: t`Location`,
      dataField: 'workLocation',
      formatter: (cell, job) => (
        <Typography variant='caption' className={styles.caption}>
          {job.workLocation}
        </Typography>
      ),
    },
    {
      width: 650,
      classes: styles.proposal,
      dataField: 'proposalsPipeline',
      formatter: (cell, job) => (
        <ProposalsPipeline pipeline={cell} openingsCount={job.openingsCount} />
      ),
    },
    {
      align: 'right',
      dataField: 'status',
      classes: styles.jobStatusWrapper,
      formatter: (status) => (
        <Badge
          text={getChoiceName(jobStatusChoices, status)}
          variant={JOB_STATUS_BADGE_COLORS[status]}
        />
      ),
    },
  ];

  const shouldShowAddJob = useIsAuthenticatedByRoles(USERS_ALLOWED_TO_CREATE_JOB);

  const handleRowClick = useCallback(
    (e, { id }) => {
      history.push(`/job/${id}`);
    },
    [history]
  );

  return (
    <DefaultPageContainer title={t`Jobs`}>
      <TableHeader
        storeKey={STORE_TABLE_KEY}
        renderRightSide={() =>
          shouldShowAddJob && (
            <Button to='/c/jobs/add' isLink>
              <Trans>Add Job</Trans>
            </Button>
          )
        }
      />

      <div className={styles.outerWrapper}>
        <div className={styles.innerWrapper}>
          <Container>
            <Table
              data={data}
              columns={columns}
              storeKey={STORE_TABLE_KEY}
              onRowClick={handleRowClick}
              isBigRow
            />
          </Container>
        </div>
      </div>
    </DefaultPageContainer>
  );
};

export default memo(JobsPage);
