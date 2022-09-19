import React, { memo } from 'react';
import { useSelector } from 'react-redux';

import { Modal, Typography } from '@components';
import { getAlertButtons } from '@utils';

import styles from './Alert.module.scss';

const Alert = () => {
  const alert = useSelector((state) => state.modals.alerts[0] ?? {});
  const isOpen = useSelector((state) => state.modals.alerts.length > 0);

  const {
    title,
    resolve,
    reject,
    description,
    content,
    getButtons = getAlertButtons,
  } = alert;

  return (
    isOpen && (
      <Modal
        title={title}
        isOpen={isOpen}
        withoutAnimation={!isOpen} // no animation on close
        onClose={reject}
        customButtons={getButtons(resolve, reject)}
      >
        <div className={styles.description}>
          {description && <Typography>{description}</Typography>}
          {content}
        </div>
      </Modal>
    )
  );
};

export default memo(Alert);
