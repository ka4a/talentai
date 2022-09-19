import React, { memo, useCallback } from 'react';
import { Container } from 'reactstrap';

import { Trans, t } from '@lingui/macro';

import { client } from '@client';
import { fetchErrorHandler } from '@utils';
import { useNotificationsList, useUserNotificationsCount } from '@swrAPI';
import {
  NotificationsList,
  DefaultPageContainer,
  Button,
  Typography,
} from '@components';

import styles from './NotificationsPage.module.scss';

const NotificationsPage = () => {
  const { mutate: refreshList } = useNotificationsList();
  const { mutate: refreshCount } = useUserNotificationsCount();

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
    <DefaultPageContainer title={t`Notifications`}>
      <div className={styles.header}>
        <Container className={styles.content}>
          <Typography variant='h1'>
            <Trans>Notifications</Trans>
          </Typography>

          <Button onClick={markAllAsRead}>
            <Trans>Mark all as read</Trans>
          </Button>
        </Container>
      </div>

      <div className={styles.notificationContainer}>
        <NotificationsList noDataMessage={t`No Notification`} />
      </div>
    </DefaultPageContainer>
  );
};

export default memo(NotificationsPage);
