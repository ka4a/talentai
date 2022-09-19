import React, { memo } from 'react';
import { MdNotifications } from 'react-icons/md';

import IconButton from '@components/UI/IconButton';
import { useUserNotificationsCount } from '@swrAPI';

import styles from './NotificationDropdown.module.scss';

const NotificationsDropdownTrigger = () => {
  const { data } = useUserNotificationsCount();
  const { count } = data;

  return (
    <div className={styles.buttonWrapper}>
      <IconButton>
        <MdNotifications size={24} />
      </IconButton>

      {count > 0 && <div className={styles.badge}>{count > 99 ? '99+' : count}</div>}
    </div>
  );
};

export default memo(NotificationsDropdownTrigger);
