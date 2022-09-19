import React, { useState, useEffect } from 'react';
import InfiniteScroll from 'react-infinite-scroll-component';

import PropTypes from 'prop-types';
import _ from 'lodash';
import moment from 'moment';

import { client } from '@client';
import { Loading } from '@components';
import { fetchErrorHandler } from '@utils';

import LogEntry from './LogEntry';

import styles from './CandidateLog.module.scss';

const LIMIT = 12;

const getFormattedLog = (items) => {
  const activities = {};
  _.forEach(items, (item) => {
    if (item.changes) {
      let updatedAt = null;
      const changes = [];

      _.forEach(item.changes, (value, key) => {
        if (key === 'updatedAt') {
          updatedAt = value.new;
        } else {
          changes.push({ name: key, ...value });
        }
      });

      if (changes.length) {
        const date = moment(updatedAt);
        const dateStr = date.format('LL');
        activities[dateStr] = activities[dateStr] || [];
        activities[dateStr].push({
          revision: item.revision,
          dateTime: updatedAt,
          actor: item.actor,
          changes: changes,
        });
      }
    }
  });
  return activities;
};

const CandidateLog = (props) => {
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [hasMore, setHasMore] = useState(true);

  async function fetchLogs(candidate, limit = null) {
    try {
      const parameters = { candidate };
      if (limit !== null) parameters.limit = limit;
      const response = await client.execute({
        operationId: 'candidate_logs_list',
        parameters,
      });
      return {
        logs: getFormattedLog(response.obj.results),
        count: response.obj.count,
      };
    } catch (error) {
      fetchErrorHandler(error);
    }
  }

  const fetchMoreLogs = () => {
    fetchLogs(props.candidateId).then(({ logs }) => {
      setHasMore(false);
      setLogs(logs);
    });
  };

  useEffect(() => {
    fetchLogs(props.candidateId, LIMIT).then(({ logs, count }) => {
      setLogs(logs);
      if (count <= LIMIT) setHasMore(false);
      setLoading(false);
    });
  }, [props.candidateId]);

  if (loading) {
    return <Loading />;
  }

  return (
    <div id='timeLineScroll' className={styles.timeLineScroll}>
      <div className={styles.timeLineCtnr}>
        <InfiniteScroll
          dataLength={logs.length || 5}
          next={fetchMoreLogs}
          hasMore={hasMore}
          loader={<Loading />}
          scrollableTarget='timeLineScroll'
        >
          {_.map(logs, (dateLogs, date) => (
            <ul className={styles.timeLine} key={date}>
              <li className={styles.timeLabel}>
                <span>{date}</span>
              </li>
              {_.map(dateLogs, (log) => (
                <LogEntry
                  changes={log.changes}
                  key={log.revision}
                  dateTime={log.dateTime}
                  actor={log.actor}
                />
              ))}
            </ul>
          ))}
        </InfiniteScroll>
      </div>
    </div>
  );
};

CandidateLog.propTypes = {
  candidateId: PropTypes.number,
};

export default CandidateLog;
