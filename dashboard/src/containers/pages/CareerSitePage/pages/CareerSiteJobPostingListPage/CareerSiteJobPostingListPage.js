import React, { memo, useCallback, useEffect, useMemo } from 'react';
import { Container } from 'reactstrap';
import { useHistory } from 'react-router-dom';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';
import useSWR from 'swr';
import classNames from 'classnames';

import {
  JobTitle,
  NotFoundTablePlaceholder,
  Table,
  TableHeader,
  Typography,
} from '@components';
import { useTable } from '@hooks';
import fetcher from '@swrAPI/fetcher';
import { JOB_EMPLOYMENT_TYPE_CHOICES } from '@constants';
import { mapChoiceNamesByValue } from '@utils';

import CareerSitePageContainer from '../../components/CareerSitePageContainer';
import NoJobPostingsPlaceholder from '../../components/NoJobPostingsPlaceholder';

import styles from './CareerSiteJobPostingListPage.module.scss';

const JOB_EMPLOYMENT_TYPE_CHOICE_MAP = mapChoiceNamesByValue(
  JOB_EMPLOYMENT_TYPE_CHOICES
);

function CareerSiteJobPostingListPage({ basePath, orgName, orgSlug }) {
  const history = useHistory();
  const { i18n } = useLingui();

  const handleRowClick = useCallback(
    (event, { slug }) => {
      history.push(`${basePath}/${slug}`);
    },
    [history, basePath]
  );

  const data = useTable({
    useGetData: useJobPostingList,
    storeKey: STORE_TABLE_KEY,
    defaultSort: 'title',
    paginationKey: 'careerSiteJobPostingsShowPer',
    params: { orgSlug },
    isPublic: true,
  });

  const isSearched = useSelector(({ table }) =>
    Boolean(table[STORE_TABLE_KEY]?.search)
  );

  const locale = useSelector(({ settings }) => settings.locale);
  const refresh = data.mutate;
  useEffect(() => {
    refresh();
  }, [locale, refresh]);

  const columns = useMemo(
    () => [
      {
        sort: true,
        width: 421,
        text: i18n._(t`Job Title`),
        dataField: 'title',
        formatter: jobTitleFormatter,
      },
      {
        width: 353,
        text: i18n._(t`Location`),
        dataField: 'workLocation',
        formatter: captionFormatter,
      },
      {
        width: 353,
        text: i18n._(t`Function`),
        dataField: 'function',
        formatter: (value) => captionFormatter(value?.title ?? ''),
      },
      {
        width: 265,
        text: i18n._(t`Employment Type`),
        dataField: 'employmentType',
        formatter: (value) =>
          captionFormatter(i18n._(JOB_EMPLOYMENT_TYPE_CHOICE_MAP[value] || '')),
      },
    ],
    [i18n]
  );

  return (
    <CareerSitePageContainer title={t`Jobs`} orgName={orgName}>
      <TableHeader storeKey={STORE_TABLE_KEY} />

      <Container>
        <Table
          isPublic
          isBigRow
          columns={columns}
          data={data}
          storeKey={STORE_TABLE_KEY}
          onRowClick={handleRowClick}
          noDataPlaceholder={
            isSearched ? (
              <NotFoundTablePlaceholder title={t`No Openings found`} />
            ) : (
              <NoJobPostingsPlaceholder />
            )
          }
        />
      </Container>
    </CareerSitePageContainer>
  );
}

const STORE_TABLE_KEY = 'careerSiteJobPostings';

function captionFormatter(value) {
  return (
    <Typography variant='caption' className={styles.caption}>
      {value}
    </Typography>
  );
}

function jobTitleFormatter(cell, jobPosting) {
  return (
    <JobTitle
      className='fs-16 d-flex'
      linkClassName={classNames(styles.jobTitle, 'text-capitalize text-medium')}
      job={jobPosting}
      link
      widthTooltip
    />
  );
}

function useJobPostingList(params) {
  const { data, error, mutate } = useSWR(
    [
      `public/career_site/${params.orgSlug}/job_postings`,
      params.search,
      params.limit,
      params.offset,
      params.ordering,
      params.workLocation,
      params.function,
      params.employmentType,
    ],
    jobPostingFetcher
  );

  return {
    data,
    loading: !data && !error,
    error,
    mutate,
  };
}

function jobPostingFetcher(
  url,
  search,
  limit,
  offset,
  ordering,
  workLocation,
  jobFunction,
  employmentType
) {
  return fetcher(url, {
    params: {
      search,
      limit,
      offset,
      ordering,
      workLocation,
      employmentType,
      function: jobFunction,
    },
  });
}

CareerSiteJobPostingListPage.propTypes = {
  orgName: PropTypes.string,
  orgSlug: PropTypes.string.isRequired,
  basePath: PropTypes.string.isRequired,
};

CareerSiteJobPostingListPage.defaultProps = {
  orgName: '',
};

export default memo(CareerSiteJobPostingListPage);
