import React, { memo } from 'react';
import { Container } from 'reactstrap';

import PropTypes from 'prop-types';

import TableSearchInput from '../TableSearchInput';

import styles from './TableHeader.module.scss';

const TableHeader = ({ renderRightSide, storeKey }) => (
  <div className={styles.searchWrapper}>
    <Container className={styles.searchContentWrapper}>
      <TableSearchInput storeKey={storeKey} />
      {renderRightSide ? renderRightSide() : null}
    </Container>
  </div>
);

TableHeader.propTypes = {
  renderRightSide: PropTypes.func,
  storeKey: PropTypes.string.isRequired,
};

TableHeader.defaultProps = {
  renderRightSide: null,
};

export default memo(TableHeader);
