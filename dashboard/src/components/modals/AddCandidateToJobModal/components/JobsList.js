import React, { memo, useCallback, useState } from 'react';
import { useSelector } from 'react-redux';

import { t, Trans } from '@lingui/macro';
import { useLingui } from '@lingui/react';
import classnames from 'classnames';

import { Badge, Button, Loading, SearchInput, Typography } from '@components';
import { useCandidatesRead, useJobsList } from '@swrAPI';
import { fetchErrorHandler } from '@utils';
import { client } from '@client';

import styles from '../AddCandidateToJobModal.module.scss';

const JobsList = () => {
  const [search, setSearch] = useState('');

  const { data: candidate } = useCandidatesRead();
  const { data: jobs, loading, mutate: refreshJobs } = useJobsList({
    search,
    status: 'open',
    checkCandidateProposed: candidate.id,
  });

  const isScrollStart = useSelector((state) => state.modals.isScrollStart);

  const { i18n } = useLingui();

  const onPropose = useCallback(
    async (job) => {
      try {
        const { id } = job;

        await client.execute({
          operationId: 'proposals_create',
          parameters: {
            data: {
              job: id,
              candidate: candidate.id,
            },
          },
        });

        await refreshJobs();
      } catch (error) {
        fetchErrorHandler(error);
      }
    },
    [candidate.id, refreshJobs]
  );

  return (
    <>
      <div
        className={classnames([
          styles.contentHeader,
          { [styles.withShadow]: !isScrollStart },
        ])}
      >
        <SearchInput
          className={styles.search}
          state={search}
          setState={setSearch}
          mode='regular'
        />
      </div>

      {loading && <Loading className={styles.loading} />}

      {jobs?.results.length > 0 && (
        <div className={styles.list}>
          {jobs.results.map((job) => (
            <div key={job.id} className={styles.item}>
              <Typography variant='bodyStrong'>{job.title}</Typography>

              {job.candidateProposed ? (
                <Badge variant='neutral' text={i18n._(t`Applied`)} />
              ) : (
                <Button variant='secondary' onClick={() => onPropose(job)}>
                  <Typography variant='button'>
                    <Trans>Add to Job</Trans>
                  </Typography>
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
};

export default memo(JobsList);
