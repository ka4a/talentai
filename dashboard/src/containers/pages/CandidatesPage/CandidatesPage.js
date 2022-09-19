import React, { memo, useCallback } from 'react';
import { useHistory, useParams } from 'react-router-dom';

import { t, Trans } from '@lingui/macro';

import { formatNumber } from '@utils';
import {
  DefaultPageContainer,
  NameAndAvatarCell,
  ModalImportCandidate,
  FormattedLanguage,
  Button,
  Table,
  TableHeader,
  CandidateCurrentJob,
  TextCell,
} from '@components';
import { useCandidatesList } from '@swrAPI';
import { useIsAuthenticatedByRoles, useScrollToTop, useTable } from '@hooks';
import { CLIENT_ADMINISTRATORS, CLIENT_INTERNAL_RECRUITERS } from '@constants';

import CandidateDetails from './components/CandidateDetails';
import CandidatePageLayout from './components/CandidatePageLayout';

const STORE_TABLE_KEY = 'candidates';

const CandidatesPage = () => {
  const history = useHistory();
  const { candidateId } = useParams();

  useScrollToTop();

  const columns = [
    {
      sort: true,
      width: 335,
      text: t`Name`,
      dataField: 'name',
      formatter: (name, candidate) => {
        const tooltipId = `candidateNameTooltip${candidate.id}`;

        return (
          <NameAndAvatarCell
            avatarSrc={candidate.photo}
            name={name}
            tooltipId={tooltipId}
          />
        );
      },
    },
    {
      width: 465,
      hideInSidebar: true,
      text: t`Current Job`,
      dataField: 'currentPosition',
      formatter: (cell, candidate) => (
        <CandidateCurrentJob candidate={candidate} withTooltip />
      ),
    },
    {
      width: 237,
      hideInSidebar: true,
      dataField: 'languages',
      text: t`Japanese Fluency`,
      formatter: (cell, candidate) => {
        const japanLanguage = candidate.languages?.find(
          (language) => language.language === 'ja'
        );

        return (
          japanLanguage && (
            <FormattedLanguage level={japanLanguage.level} countryCode='JP' />
          )
        );
      },
    },
    {
      sort: true,
      width: 238,
      dataField: 'salary',
      hideInSidebar: true,
      text: t`Desired Salary`,
      formatter: (cell, candidate) => (
        <TextCell>
          {formatNumber({
            value: candidate.salary,
            currency: candidate.salaryCurrency,
          })}
        </TextCell>
      ),
    },
    {
      sort: true,
      width: 222,
      text: t`Source`,
      dataField: 'source',
      formatter: (cell, candidate, { isActive }) => (
        <TextCell isActive={isActive}>{cell}</TextCell>
      ),
    },
  ];

  const data = useTable({
    useGetData: useCandidatesList,
    paginationKey: 'candidatesShowPer',
    defaultSort: '-createdAt',
    storeKey: STORE_TABLE_KEY,
  });

  const closeCandidate = useCallback(() => {
    history.push(`/candidates`);
  }, [history]);

  const handleRowClick = useCallback(
    (e, { id }) => {
      history.push(`/candidate/${id}`);
    },
    [history]
  );

  const shouldShowAddCandidate = useIsAuthenticatedByRoles([
    CLIENT_ADMINISTRATORS,
    CLIENT_INTERNAL_RECRUITERS,
  ]);

  // TODO(ZOO-1025)
  const canImport = false;
  // const { user } = this.props;
  // const canImport = Boolean(
  //   user.profile.org.hasZohoIntegration || window.extInstalled
  // );

  return (
    <DefaultPageContainer title={t`Candidates`}>
      <div className='candidate-page'>
        <CandidatePageLayout
          isOpen={Boolean(candidateId)}
          onClose={closeCandidate}
          header={
            <TableHeader
              storeKey={STORE_TABLE_KEY}
              renderRightSide={() => (
                <>
                  <ModalImportCandidate showTrigger={canImport} onSuccess={data.mutate}>
                    <Button>
                      <Trans>Import</Trans>
                    </Button>
                  </ModalImportCandidate>

                  {shouldShowAddCandidate && (
                    <Button to='/candidates/add' isLink>
                      <Trans>Add Candidate</Trans>
                    </Button>
                  )}
                </>
              )}
            />
          }
          renderTable={({ areDetailsOpen, hideHeader }) => (
            <Table
              data={data}
              columns={columns}
              storeKey={STORE_TABLE_KEY}
              onRowClick={handleRowClick}
              isOpenColumn={areDetailsOpen}
              hideHeader={hideHeader}
              activeRowId={Number(candidateId)}
            />
          )}
          renderDetails={() => <CandidateDetails />}
        />
      </div>
    </DefaultPageContainer>
  );
};

export default memo(CandidatesPage);
