import React, { memo, useCallback } from 'react';
import { useLocation, useHistory } from 'react-router-dom';
import { Dropdown, DropdownMenu, DropdownToggle } from 'reactstrap';
import { useToggle } from 'react-use';

import { Trans } from '@lingui/macro';

import { client } from '@client';
import { fetchErrorHandler } from '@utils';
import { useNotificationsList, useUserNotificationsCount } from '@swrAPI';
import { Typography, Button, NotificationsList } from '@components';

import NavItemNotifications from './NotificationsDropdownTrigger';

import styles from './NotificationDropdown.module.scss';

const NotificationsDropdown = () => {
  const [isOpen, toggle] = useToggle(false);

  const { mutate: refreshList } = useNotificationsList();
  const { mutate: refreshCount } = useUserNotificationsCount();

  const history = useHistory();
  const { pathname } = useLocation();

  const toggleDropdown = useCallback(async () => {
    if (pathname !== '/notifications' || isOpen) {
      if (!isOpen) await refreshCount();
      toggle();
    }
  }, [isOpen, pathname, refreshCount, toggle]);

  const goToNotificationsPage = useCallback(() => {
    history.push('/notifications');
    toggle(false);
  }, [history, toggle]);

  const onLinkClick = useCallback(() => {
    toggle(false);
  }, [toggle]);

  const markAllAsRead = useCallback(async () => {
    try {
      await client.execute({
        operationId: 'notifications_mark_all_as_read',
      });

      await Promise.all([refreshList(), refreshCount()]);
    } catch (error) {
      fetchErrorHandler(error);
    }
  }, [refreshCount, refreshList]);

  return (
    <Dropdown direction='down' isOpen={isOpen} toggle={toggleDropdown}>
      <DropdownToggle className={styles.trigger} color='link'>
        <NavItemNotifications />
      </DropdownToggle>

      <DropdownMenu className={styles.container} right>
        {isOpen && (
          <div>
            <div className={styles.header}>
              <Typography variant='subheading'>
                <Trans>Notifications</Trans>
              </Typography>

              <Button
                onClick={markAllAsRead}
                className={styles.notificationButton}
                variant='text'
              >
                <Trans>Mark all as read</Trans>
              </Button>
            </div>

            <div className={styles.list}>
              <NotificationsList onLinkClick={onLinkClick} hidePagination />
            </div>

            <div className={styles.seeAll}>
              <Button
                variant='text'
                className={styles.notificationButton}
                onClick={goToNotificationsPage}
              >
                <Trans>See all</Trans>
              </Button>
            </div>
          </div>
        )}
      </DropdownMenu>
    </Dropdown>
  );
};

export default memo(NotificationsDropdown);
