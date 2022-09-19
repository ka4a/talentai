import React, { memo, useContext, useEffect } from 'react';
import { usePrevious } from 'react-use';

import { noop } from 'lodash';
import PropTypes from 'prop-types';

import { Modal } from '@components';
import { FormContext } from '@contexts';

import JobPostingForm from '../JobPostingForm/JobPostingForm';

function JobPostingModal(props) {
  const { title, isOpen, onClose } = props;

  const { resetForm, onSubmit } = useContext(FormContext);
  const wasOpen = usePrevious(isOpen);

  useEffect(() => {
    if (!wasOpen && isOpen) resetForm();
  }, [isOpen, wasOpen, resetForm]);

  return (
    <Modal
      size='large'
      title={title}
      isOpen={isOpen}
      onSave={onSubmit}
      onClose={onClose}
      // Cancel button only appears if function is passed
      // But we only need to close modal, which it does for cancel button always
      onCancel={noop}
    >
      <JobPostingForm />
    </Modal>
  );
}

export const JobPostingModalControlProps = {
  isOpen: PropTypes.bool,
  isEnabled: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
  openConfirmDisableDialog: PropTypes.func.isRequired,
};

JobPostingModal.propTypes = {
  ...JobPostingModalControlProps,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  renderForm: PropTypes.func.isRequired,
};

JobPostingModal.defaultProps = {
  isOpen: false,
  isEnabled: false,
};

export default memo(JobPostingModal);
