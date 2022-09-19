import React from 'react';
import { UncontrolledTooltip } from 'reactstrap';

import classnames from 'classnames';
import PropTypes from 'prop-types';
import _ from 'lodash';
import { Trans } from '@lingui/macro';

import Avatar from '../UI/Avatar';

import styles from './AvatarList.module.scss';

export default function AvatarList(props) {
  const { users, max, onAdd, size } = props;

  const z_index = max ? 10 + max : 10;

  const toDisplayUsers = max ? _.slice(users, 0, max) : users;
  const countDiff = users.length - toDisplayUsers.length;

  return (
    <>
      <div className={classnames(styles.container)}>
        {_.map(toDisplayUsers, (user, i) => (
          <>
            <Avatar
              size={size}
              id={`user-name-${user.id}`}
              src={user.photo}
              className={classnames(styles.item)}
              style={{ zIndex: z_index - i }}
              user={user}
            />
            <UncontrolledTooltip
              placement='bottom'
              hideArrow
              target={`user-name-${user.id}`}
            >
              {[user.firstName, user.lastName].join(' ')}
            </UncontrolledTooltip>
          </>
        ))}
        {onAdd ? (
          <Avatar
            size={size}
            onClick={onAdd}
            className={classnames(styles.item, styles['new-item'])}
            style={{ zIndex: z_index - toDisplayUsers.length }}
            newUser
          />
        ) : null}
      </div>
      {max && countDiff ? (
        <span className='text-secondary'>
          <Trans>and {countDiff} more</Trans>
        </span>
      ) : null}
    </>
  );
}

AvatarList.propTypes = {
  users: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      firstName: PropTypes.string,
      lastName: PropTypes.string,
    })
  ),
  size: PropTypes.string,
  max: PropTypes.number,
};

AvatarList.defaultProps = {
  users: [],
  max: 5,
};
