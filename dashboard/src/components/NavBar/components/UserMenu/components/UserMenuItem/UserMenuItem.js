import React from 'react';
import { DropdownItem } from 'reactstrap';

import Typography from '@components/UI/Typography';

import styles from './UserMenuItem.module.scss';

function UserMenuItem({ children, ...rest }) {
  return (
    <DropdownItem className={styles.root} {...rest}>
      <Typography variant='button'>{children}</Typography>
    </DropdownItem>
  );
}

export default UserMenuItem;
