import React, { memo, useMemo } from 'react';

import sortBy from 'lodash/sortBy';

import { ReqStatus, Typography, Avatar, JapaneseName } from '@components';
import { useProposalsRead } from '@swrAPI';

import ProposalComments from '../ProposalComments';
import ProposalTabs from '../ProposalTabs';

import styles from './Proposal.module.scss';

const commentDefaultParams = { publicTab: false, limit: 10 };

const useGetComments = () => {
  const { data, mutate } = useProposalsRead();

  const comments = data.comments ?? [];
  const sortedComments = sortBy(comments, 'createdAt');

  return {
    comments: sortedComments,
    count: comments.length,
    mutate,
  };
};

const Proposal = () => {
  const proposal = useProposalsRead();
  const comments = useGetComments();

  const { candidate = {}, createdBy = {}, source = {} } = proposal.data;
  const {
    firstNameKanji,
    lastNameKanji,
    firstNameKatakana,
    lastNameKatakana,
  } = candidate;

  const submittedBy = useMemo(() => {
    const { name, organizationType } = source;

    const createdByName = `${createdBy.firstName} ${createdBy.lastName}`;
    const submittedByAgency = organizationType !== 'client' ? ` from ${name}` : '';

    return `Created by ${createdByName}${submittedByAgency}`;
  }, [createdBy.firstName, createdBy.lastName, source]);

  if (proposal.loading || proposal.error) {
    return (
      <div className={styles.loading}>
        <ReqStatus loading={proposal.loading} error={proposal.error} inline />
      </div>
    );
  }

  return (
    <div className={styles.proposalWrapper}>
      <div className={styles.header}>
        <Avatar
          shape='circle'
          src={candidate.photo}
          size='sm'
          style={{
            marginRight: '20px',
          }}
        />

        <div className={styles.headerContent}>
          <div className={styles.controls} />

          <div>
            <Typography variant='h1' className={styles.name}>
              {candidate.name}
            </Typography>

            <JapaneseName
              kanjiFirst={firstNameKanji}
              kanjiLast={lastNameKanji}
              katakanaFirst={firstNameKatakana}
              katakanaLast={lastNameKatakana}
            />
          </div>

          <Typography variant='bodyStrong' className={styles.submittedBy}>
            {submittedBy}
          </Typography>
        </div>
      </div>

      <ProposalTabs>
        {/* todo: move it inside of Proposal component when work on comments */}
        <ProposalComments
          proposal={proposal.data}
          commentsParams={commentDefaultParams}
          commentsData={comments}
          onChange={comments.mutate}
        />
      </ProposalTabs>
    </div>
  );
};

export default memo(Proposal);
