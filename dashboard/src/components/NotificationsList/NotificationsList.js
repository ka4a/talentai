import React, { memo, useCallback } from 'react';
import { useLocation, useHistory } from 'react-router-dom';
import { FaCircle } from 'react-icons/fa';

import PropTypes from 'prop-types';

import { client } from '@client';
import { useTable } from '@hooks';
import { fetchErrorHandler } from '@utils';
import { useNotificationsList, useUserNotificationsCount } from '@swrAPI';
import { Typography, HumanizedDate, Button, Table } from '@components';

import styles from './NotificationsList.module.scss';

const STORE_TABLE_KEY = 'notifications';

const NotificationsList = ({ onLinkClick, hidePagination, noDataMessage }) => {
  const data = useTable({
    useGetData: useNotificationsList,
    paginationKey: 'notificationsShowPer',
    defaultSort: '-timestamp',
    storeKey: STORE_TABLE_KEY,
  });
  const { mutate: refreshCount } = useUserNotificationsCount();

  const history = useHistory();
  const { pathname } = useLocation();

  const markAsRead = useCallback(
    async (id) => {
      try {
        await client.execute({
          operationId: 'notifications_mark_as_read',
          parameters: { id },
        });

        await Promise.all([data.mutate(), refreshCount()]);
      } catch (error) {
        fetchErrorHandler(error);
      }
    },
    [data, refreshCount]
  );

  const onRowClick = useCallback(
    (cell, row) => {
      if (row.link) {
        onLinkClick(row);
        history.push(row.link);
      }
      row.unread && markAsRead(row.id);
    },
    [history, markAsRead, onLinkClick]
  );

  const columns = [
    {
      dataField: 'unread',
      align: 'right',
      classes: 'pl-2 pr-0 align-baseline',
      formatter: (cell, notification) =>
        notification.unread && (
          <Button
            variant='dot'
            title='Mark as read'
            onClick={async () => {
              await markAsRead(notification.id);
            }}
          >
            <FaCircle size={14} />
          </Button>
        ),
    },
    {
      dataField: 'verb',
      formatter: (cell, notification) => (
        <div className='fs-14'>
          <span className={'font-weight-normal'}>
            <Typography variant='caption'>{notification.text}</Typography>
          </span>

          <Typography variant='caption' className={styles.timeAgo}>
            <HumanizedDate date={notification.timestamp} />
          </Typography>
        </div>
      ),
    },
  ];

  return (
    <Table
      data={data}
      columns={columns}
      className={
        pathname !== '/notifications' ? styles.borderlessTable : styles.fullWidthTable
      }
      hidePagination={hidePagination}
      noDataMessage={noDataMessage}
      storeKey={STORE_TABLE_KEY}
      onRowClick={onRowClick}
      withBorder={false}
      hideHeader
    />
  );
};

NotificationsList.propTypes = {
  onLinkClick: PropTypes.func,
  noDataMessage: PropTypes.string,
  hidePagination: PropTypes.bool,
};

NotificationsList.defaultProps = {
  onLinkClick: () => {},
  noDataMessage: '',
  hidePagination: false,
};

export default memo(NotificationsList);
