import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import { ReactComponent as TrashCan } from '@images/icons/trash-can.svg';

import styles from './ListItemCard.module.scss';

const ListItemCard = ({ index, children, onRemove, isRemoveDisabled }) => (
  <div className={styles.wrapper}>
    <div className={styles.header}>
      <div className={styles.order}>{index + 1}</div>
      <TrashCan
        className={classnames([
          styles.deleteButton,
          { [styles.disabled]: isRemoveDisabled },
        ])}
        onClick={onRemove}
      />
    </div>

    <div className={styles.content}>{children}</div>
  </div>
);

ListItemCard.propTypes = {
  index: PropTypes.number.isRequired,
  children: PropTypes.node.isRequired,
  onRemove: PropTypes.func.isRequired,
  isRemoveDisabled: PropTypes.bool,
};

ListItemCard.defaultProps = {
  isRemoveDisabled: false,
};

export default memo(ListItemCard);
