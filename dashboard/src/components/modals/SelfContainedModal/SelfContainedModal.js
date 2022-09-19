import React, { memo, useState, useMemo } from 'react';
import { Modal, ModalBody } from 'reactstrap';
import ModalHeader from 'reactstrap/es/ModalHeader';

import PropTypes from 'prop-types';

const invert = (value) => !value;

function useModalActions(setValue, value) {
  return useMemo(
    () => ({
      open: () => setValue(true),
      close: () => setValue(false),
      toggle: () => setValue(invert),
    }),
    [setValue]
  );
}

SelfContainedModal.propTypes = {
  renderHeader: PropTypes.func,
  renderTrigger: PropTypes.func,
  renderContent: PropTypes.func,
  isOpen: PropTypes.bool,
  setIsOpen: PropTypes.func,
  size: PropTypes.string,
  onClosed: PropTypes.func,
};

function SelfContainedModal(props) {
  const { renderHeader, renderTrigger, renderContent, size, onClosed } = props;

  let [isOpen, setIsOpen] = useState(false);

  if (props.setIsOpen != null) {
    isOpen = props.isOpen;
    setIsOpen = props.setIsOpen;
  }

  const modal = useModalActions(setIsOpen);

  return (
    <>
      {renderTrigger ? renderTrigger(modal.open) : null}
      <Modal isOpen={isOpen} toggle={modal.toggle} size={size} onClosed={onClosed}>
        {renderHeader && isOpen ? (
          <ModalHeader toggle={modal.toggle}>{renderHeader(modal)}</ModalHeader>
        ) : null}
        <ModalBody>{renderContent && isOpen ? renderContent(modal) : null}</ModalBody>
      </Modal>
    </>
  );
}

export default memo(SelfContainedModal);
