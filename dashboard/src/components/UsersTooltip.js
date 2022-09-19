import React, { useState } from 'react';
import { Tooltip } from 'reactstrap';

import _ from 'lodash';

import UserInline from './UserInline';

export default function UsersTooltip({ users }) {
  // eslint-disable-next-line
  const [tooltipId, settooltipId] = useState(() => _.uniqueId('UsersTooltip'));
  const [isOpen, setIsOpen] = useState(false);

  const toggleIsOpen = () => {
    setIsOpen(!isOpen);
  };

  if (users.length === 0) {
    return <span>-</span>;
  }

  return (
    <>
      <div id={tooltipId}>
        {_.chain(users)
          .slice(0, 2)
          .map((u, i) => (
            <div key={i}>
              <UserInline user={u} />
              {i === 1 && users.length > 2 ? ' ...' : null}
            </div>
          ))
          .value()}
      </div>
      <Tooltip
        placement='bottom-start'
        hideArrow
        innerClassName='users-tooltip'
        autohide={false}
        isOpen={isOpen}
        target={tooltipId}
        toggle={toggleIsOpen}
      >
        {_.map(users, (u, i) => (
          <div key={i}>
            <UserInline user={u} />
          </div>
        ))}
      </Tooltip>
    </>
  );
}
