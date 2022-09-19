import React, { memo } from 'react';

import PropTypes from 'prop-types';

import Typography from '../../UI/Typography';

import styles from './JapaneseName.module.scss';

const JapaneseName = (props) => {
  const { kanjiFirst, kanjiLast, katakanaFirst, katakanaLast } = props;

  return (
    <>
      {kanjiFirst && <Typography className={styles.firstName}>{kanjiFirst}</Typography>}

      <Typography>{kanjiLast}</Typography>

      <div className={styles.divider} />

      {katakanaFirst && (
        <Typography className={styles.firstName}>{katakanaFirst}</Typography>
      )}

      <Typography>{katakanaLast}</Typography>
    </>
  );
};

JapaneseName.propTypes = {
  kanjiFirst: PropTypes.string,
  kanjiLast: PropTypes.string,
  katakanaFirst: PropTypes.string,
  katakanaLast: PropTypes.string,
};

JapaneseName.defaultProps = {
  kanjiFirst: '',
  kanjiLast: '',
  katakanaFirst: '',
  katakanaLast: '',
};

export default memo(JapaneseName);
