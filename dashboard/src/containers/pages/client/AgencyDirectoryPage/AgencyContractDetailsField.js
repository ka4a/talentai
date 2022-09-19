import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import styles from './AgencyDirectory.module.scss';

function AgencyContractDetailsField({ children, title, isWide }) {
  return (
    <div
      className={classnames(styles.detailsField, { [styles.detailsFieldWide]: isWide })}
    >
      <div className={styles.detailsFieldTitle}>{title}</div>
      <div className={styles.detailsFieldValue}>{children}</div>
    </div>
  );
}

AgencyContractDetailsField.propTypes = {
  title: PropTypes.string,
  isWide: PropTypes.bool,
};
AgencyContractDetailsField.defaultProps = {
  title: '',
  isWide: false,
};

export default memo(AgencyContractDetailsField);
