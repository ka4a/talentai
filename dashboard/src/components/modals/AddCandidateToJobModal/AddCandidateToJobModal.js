import React, { memo, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useLockBodyScroll } from 'react-use';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { Modal } from '@components';
import { closeAddCandidateToJob } from '@actions';

import CandidatesList from './components/CandidatesList';
import JobsList from './components/JobsList';

import styles from './AddCandidateToJobModal.module.scss';

const AddCandidateToJobModal = ({ listMode }) => {
  const { isOpen } = useSelector((state) => state.modals.addCandidateToJob);

  const dispatch = useDispatch();

  const closeModal = useCallback(() => {
    dispatch(closeAddCandidateToJob());
  }, [dispatch]);

  useLockBodyScroll(isOpen);

  return (
    <Modal
      isOpen={isOpen}
      title={t`Add Candidate to Job`}
      onClose={closeModal}
      onSave={closeModal}
      saveText={t`Done`}
    >
      <div className={styles.content}>
        {listMode === 'candidates' && <CandidatesList />}
        {listMode === 'jobs' && <JobsList />}
      </div>
    </Modal>
  );
};

AddCandidateToJobModal.propTypes = {
  listMode: PropTypes.oneOf(['jobs', 'candidates']).isRequired,
};

export default memo(AddCandidateToJobModal);
