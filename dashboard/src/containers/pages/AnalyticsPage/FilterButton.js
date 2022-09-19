import React from 'react';

import classnames from 'classnames';

import styles from './FilterButton.module.css';

export default function FilterButton({ className, selected, children, ...props }) {
  return (
    <button
      type='button'
      className={classnames(
        selected ? styles.buttonSelected : styles.button,
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
