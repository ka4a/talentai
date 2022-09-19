import React, { memo, useCallback, useState } from 'react';
import { useSelector } from 'react-redux';
import { useMountedState, useToggle } from 'react-use';

import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';

import {
  Badge,
  Button,
  Typography,
  SearchInput,
  CandidatePreviewModal,
  Loading,
} from '@components';
import { client } from '@client';
import { fetchErrorHandler } from '@utils';
import { useCandidatesList, useGetJob, useProposalsList } from '@swrAPI';

import QuickAddCandidateModal from '../../QuickAddCandidateModal';

import styles from '../AddCandidateToJobModal.module.scss';

const CREATE_STAGE = 'associated';

const CandidatesList = () => {
  const [proposedIDs, setProposedIDs] = useState([]);
  const [search, setSearch] = useState('');
  const [previewCandidateId, setPreviewCandidateId] = useState(null);

  const { data: job, mutate: refreshJob } = useGetJob();
  const { mutate: refreshStages } = useProposalsList();
  const { data: candidates, mutate: refreshCandidates, loading } = useCandidatesList({
    search,
    ordering: 'name',
    checkProposedTo: job.id,
  });

  const isScrollStart = useSelector((state) => state.modals.isScrollStart);

  const isMounted = useMountedState();
  const onPropose = useCallback(
    async (candidateId) => {
      try {
        await client.execute({
          operationId: 'proposals_create',
          parameters: {
            data: {
              job: job.id,
              candidate: candidateId,
              stage: CREATE_STAGE,
            },
          },
        });

        // candidatesList is refreshed on QuickAddModal closing
        await Promise.all([refreshJob(), refreshStages()]);

        if (isMounted()) {
          setProposedIDs((prevIDs) => [...prevIDs, candidateId]);
        }
      } catch (error) {
        fetchErrorHandler(error);
      }
    },
    [isMounted, job.id, refreshJob, refreshStages]
  );

  const quickAddModal = useQuickAddModal(onPropose, refreshCandidates);

  const clearCandidate = useCallback(() => setPreviewCandidateId(null), []);

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

        <Button className={styles.createCandidateButton} onClick={quickAddModal.toggle}>
          <Trans>Create a Candidate</Trans>
        </Button>
      </div>

      {loading && <Loading className={styles.loading} />}

      {candidates?.results.length > 0 && (
        <div className={styles.list}>
          {candidates.results.map((candidate) => (
            <div key={candidate.id} className={styles.item}>
              <div className={styles.nameWrapper}>
                <Typography
                  className={styles.name}
                  variant='bodyStrong'
                  onClick={() => setPreviewCandidateId(candidate.id)}
                >
                  {candidate.name}
                </Typography>

                {candidate.currentCompany && (
                  <Typography className={styles.company} variant='caption'>
                    {candidate.currentCompany}
                  </Typography>
                )}
              </div>

              {!candidate.proposed && !proposedIDs.includes(candidate.id) ? (
                <Button variant='secondary' onClick={() => onPropose(candidate.id)}>
                  <Trans>Add to Job</Trans>
                </Button>
              ) : (
                <Badge variant='neutral' text={t`Applied`} />
              )}
            </div>
          ))}
        </div>
      )}

      <QuickAddCandidateModal modalData={quickAddModal} />

      {previewCandidateId && (
        <CandidatePreviewModal
          candidateId={previewCandidateId}
          toggle={clearCandidate}
        />
      )}
    </>
  );
};

const useQuickAddModal = (onPropose, refreshCandidates) => {
  const [isOpen, toggle] = useToggle(false);

  const ownToggle = useCallback(() => {
    if (isOpen) refreshCandidates();
    toggle();
  }, [isOpen, refreshCandidates, toggle]);

  const addCandidate = useCallback(
    async (candidate) => {
      await onPropose(candidate.id);
    },
    [onPropose]
  );

  return { isOpen, toggle: ownToggle, addCandidate };
};

export default memo(CandidatesList);
