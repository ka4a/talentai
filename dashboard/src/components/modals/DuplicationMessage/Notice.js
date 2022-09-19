import React, { memo } from 'react';

import PropTypes from 'prop-types';

import CandidateDuplicate from './CandidateDuplicate';
import LocalPropTypes from './localPropTypes';

import styles from './Notice.module.scss';

function Notice(props) {
  const { list, children } = props;

  if (list.length < 1) return null;

  return (
    <div className={styles.container}>
      <div className={styles.title}>{children}</div>
      <div className={styles.duplicates}>
        {list.map((candidate) => (
          <CandidateDuplicate key={candidate.id} {...candidate} />
        ))}
      </div>
    </div>
  );
}

Notice.propTypes = {
  list: PropTypes.arrayOf(LocalPropTypes.candidate),
};
Notice.defaultProps = {
  list: [],
};

export default memo(Notice);
