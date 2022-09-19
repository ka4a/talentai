import React from 'react';

import PropTypes from 'prop-types';

import Typography from '@components/UI/Typography';

import styles from './DetailsSection.module.scss';

function DetailsSection({ children, title }) {
  return (
    <div className={styles.root}>
      {title && (
        <Typography variant='subheading' className={styles.title}>
          {title}
        </Typography>
      )}
      {children}
    </div>
  );
}

DetailsSection.propTypes = {
  title: PropTypes.string,
};

DetailsSection.defaultProps = {
  title: null,
};

export default DetailsSection;
