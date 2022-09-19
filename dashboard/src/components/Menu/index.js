import React, { memo } from 'react';
import { Nav } from 'reactstrap';
import { BsFillBagFill, BsFillPeopleFill, BsPersonSquare } from 'react-icons/bs';

import { t } from '@lingui/macro';

import { AGENCY_GROUPS, CLIENT_GROUPS } from '@constants';

import ShowAuthenticated from '../auth/ShowAuthenticated';
import MenuItem from './MenuItem';

export const Menu = () => {
  return (
    <Nav navbar>
      <ShowAuthenticated groups={CLIENT_GROUPS}>
        <MenuItem
          title={t`Jobs`}
          link='/c/jobs'
          regex={RE_JOBS}
          icon={<BsFillBagFill />}
        />
      </ShowAuthenticated>
      <ShowAuthenticated groups={AGENCY_GROUPS}>
        <MenuItem
          title={t`Jobs`}
          link='/a/jobs'
          regex={RE_JOBS}
          icon={<BsFillBagFill />}
        />
      </ShowAuthenticated>
      <ShowAuthenticated>
        <MenuItem
          title={t`Candidates`}
          link='/candidates'
          regex={RE_CANDIDATES}
          icon={<BsFillPeopleFill />}
        />
      </ShowAuthenticated>
      <ShowAuthenticated groups={CLIENT_GROUPS}>
        <MenuItem
          title={t`Users`}
          link='/users'
          regex={RE_USERS}
          icon={<BsPersonSquare />}
        />
      </ShowAuthenticated>
    </Nav>
  );
};

const RE_JOBS = /\/jobs?/;
const RE_CANDIDATES = /\/candidates?/;
const RE_USERS = /\/users?/;

export default memo(Menu);
