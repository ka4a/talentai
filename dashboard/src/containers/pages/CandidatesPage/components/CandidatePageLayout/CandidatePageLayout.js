import React from 'react';

import TableDetailsLayout from '@components/Layouts/TableDetailsLayout';

import styles from './CandidatePageLayout.module.scss';

function CandidatePageLayout(props) {
  return (
    <TableDetailsLayout
      {...props}
      wrapperClassName={styles.wrapper}
      detailsWrapperClassName={styles.details}
      detailsClosedInnerWrapperClassName={styles.innerWrapperDetailsClosed}
    />
  );
}

export default CandidatePageLayout;
