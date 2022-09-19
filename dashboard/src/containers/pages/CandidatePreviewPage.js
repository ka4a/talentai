import React, { useCallback } from 'react';
import { Button, Badge } from 'reactstrap';

import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import {
  CandidatePreview,
  ReqStatus,
  HumanizedDate,
  DefaultPageContainer,
} from '@components';
import { useSwagger } from '@hooks';
import { client } from '@client';
import { fetchErrorHandler, confirmDeletionCandidate } from '@utils';

function CandidatePreviewPage(props) {
  const {
    i18n,
    history,
    match: {
      params: { candidateId },
    },
  } = props;

  const title = i18n._(t`Preview Candidate #${candidateId}`);

  const redirectToEditPage = useCallback(() => {
    history.push(`/candidate/${candidateId}/edit`);
  }, [candidateId, history]);

  const { obj: candidate, loading, errorObj } = useSwagger('candidates_read', {
    id: candidateId,
  });

  if (!candidate || errorObj) {
    return <ReqStatus {...{ loading, error: errorObj }} />;
  }

  if (!candidate.archived) redirectToEditPage();

  async function deleteCandidate() {
    try {
      await confirmDeletionCandidate();
      await client.execute({
        operationId: 'candidates_delete',
        parameters: { id: candidateId },
      });
      history.push('/candidates');
    } catch (error) {
      if (error.response) {
        fetchErrorHandler(error);
      }
    }
  }

  function restoreCandidate() {
    client
      .execute({
        operationId: 'candidate_restore',
        parameters: { id: candidateId, data: {} },
      })
      .then(redirectToEditPage)
      .catch(fetchErrorHandler);
  }

  return (
    <DefaultPageContainer
      title={title}
      colAttrs={{ xs: 12, md: { size: 8, offset: 2 } }}
    >
      <Badge className='mb-3' color='warning'>
        <span className='fs-20'>Archived</span>
      </Badge>
      <CandidatePreview candidate={candidate} />
      <div className='mt-5 d-flex justify-content-between align-items-center'>
        <div>
          <b>
            <Trans>Last activity</Trans>
          </b>
          : <HumanizedDate date={candidate.updatedAt} />
        </div>
        <div>
          <Button color='primary' onClick={restoreCandidate}>
            <Trans>Restore</Trans>
          </Button>
          <Button color='danger' className='ml-2' onClick={deleteCandidate}>
            <Trans>Delete</Trans>
          </Button>
        </div>
      </div>
    </DefaultPageContainer>
  );
}

export default withI18n()(CandidatePreviewPage);
