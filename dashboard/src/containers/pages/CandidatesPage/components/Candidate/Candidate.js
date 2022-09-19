import React, { useCallback, useMemo, memo } from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';

import { Trans, t } from '@lingui/macro';

import { useCandidatesRead } from '@swrAPI';
import { openAddCandidateToJob } from '@actions';
import { CLIENT_INTERNAL_RECRUITERS, CLIENT_ADMINISTRATORS } from '@constants';
import {
  CandidateDetailsTab,
  Button,
  Tabs,
  AddCandidateToJobModal,
  JapaneseName,
  ShowAuthenticated,
  PersonDetailsHeader,
} from '@components';

import CandidateInfoRow from '../CandidateInfoRow';

const Candidate = () => {
  const { candidateId } = useParams();
  const { data: candidate } = useCandidatesRead();

  const dispatch = useDispatch();
  const openAddCandidateToJobModal = useCallback(() => {
    dispatch(openAddCandidateToJob());
  }, [dispatch]);

  const fullName = useMemo(
    () => [candidate.firstName, candidate.middleName, candidate.lastName].join(' '),
    [candidate]
  );

  const {
    firstNameKanji,
    lastNameKanji,
    firstNameKatakana,
    lastNameKatakana,
  } = candidate;

  return (
    <>
      <PersonDetailsHeader
        shouldControlsOverlapTabs
        avatarSrc={candidate.photo}
        title={fullName}
        controls={
          <ShowAuthenticated
            groups={[CLIENT_INTERNAL_RECRUITERS, CLIENT_ADMINISTRATORS]}
          >
            <Button onClick={openAddCandidateToJobModal}>
              <Trans>Add Candidate to Job</Trans>
            </Button>

            <Button variant='secondary' to={`/candidate/${candidateId}/edit`} isLink>
              <Trans>Edit</Trans>
            </Button>
          </ShowAuthenticated>
        }
      >
        <JapaneseName
          kanjiFirst={firstNameKanji}
          kanjiLast={lastNameKanji}
          katakanaFirst={firstNameKatakana}
          katakanaLast={lastNameKatakana}
        />
        <CandidateInfoRow
          position={candidate?.currentPosition}
          city={candidate?.currentCity}
          prefecture={candidate?.currentPrefecture}
          salary={candidate?.totalAnnualSalary}
          currency={candidate?.currentSalaryCurrency}
        />
      </PersonDetailsHeader>

      <div className='candidate-details'>
        <Tabs tabs={TABS} />
      </div>

      <AddCandidateToJobModal listMode='jobs' />
    </>
  );
};

const TABS = [
  {
    title: t`Candidate Details`,
    id: 1,
    component: <CandidateDetailsTab />,
  },
];

export default memo(Candidate);
