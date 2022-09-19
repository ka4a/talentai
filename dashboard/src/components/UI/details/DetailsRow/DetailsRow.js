import React from 'react';

import styles from './DetailsRow.module.scss';

function DetailsRow({ children }) {
  return <div className={styles.root}>{children}</div>;
}

export default DetailsRow;
