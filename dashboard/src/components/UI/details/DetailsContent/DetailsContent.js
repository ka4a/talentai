import React from 'react';

import styles from './DetailsContent.module.scss';

function DetailsContent({ children }) {
  return <div className={styles.root}>{children}</div>;
}

export default DetailsContent;
