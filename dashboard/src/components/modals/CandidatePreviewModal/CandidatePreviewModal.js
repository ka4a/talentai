import React, { memo } from 'react';
import { Modal, ModalHeader, ModalBody } from 'reactstrap';

import { Trans } from '@lingui/macro';

import { useSwagger } from '@hooks';

import Resume from './Resume';
import CandidatePreview from '../../candidates/CandidatePreview';
import HumanizedDate from '../../format/HumanizedDate';
import ReqStatus from '../../ReqStatus';
import Typography from '../../UI/Typography';
import CandidateIconPanel from '../../candidates/CandidateIconPanel';

import styles from './CandidatePreviewModal.module.scss';

const CandidatePreviewModal = ({ toggle, candidateId }) => {
  const isOpen = Boolean(candidateId);

  const { obj: candidate, loading, errorObj } = useSwagger('candidates_read', {
    id: candidateId,
  });

  return (
    <Modal
      contentClassName={styles.modalContent}
      isOpen={isOpen}
      onClosed={toggle}
      toggle={toggle}
      size='lg'
    >
      <ModalHeader toggle={toggle} className={styles.modalBody}>
        {!candidate || errorObj ? (
          <ReqStatus {...{ error: errorObj, loading }} inline />
        ) : (
          <Typography variant='h2'>
            <>
              <span>{candidate.name}</span>
              {candidate.firstNameKanji && (
                <span className='ml-2'>({candidate.nameJa})</span>
              )}
            </>
          </Typography>
        )}

        <CandidateIconPanel
          className='text-secondary font-weight-normal'
          isExpanded
          candidate={candidate}
        />
      </ModalHeader>

      <ModalBody className={styles.modalBody}>
        {!candidate || errorObj ? (
          <ReqStatus {...{ error: errorObj, loading }} inline />
        ) : (
          <>
            <CandidatePreview candidate={candidate} className='pr-24' />
            <div className='mt-3'>
              <b>
                <Trans>Last activity</Trans>
              </b>
              : <HumanizedDate date={candidate.updatedAt} />
            </div>
          </>
        )}
      </ModalBody>

      {candidate && candidate.resume && <Resume candidateId={candidate.id} />}
    </Modal>
  );
};

export default memo(CandidatePreviewModal);
