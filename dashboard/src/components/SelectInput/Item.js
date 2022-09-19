import React from 'react';
import { DropdownItem } from 'reactstrap';

import classnames from 'classnames';

import styles from './Item.module.scss';

export default function Item({ children, value, onSelect, selected }) {
  return (
    <DropdownItem
      className={classnames(styles.item, { [styles.selected]: selected })}
      onClick={onSelect}
    >
      {children}
    </DropdownItem>
  );
}
