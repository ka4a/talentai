import React, { memo, useMemo } from 'react';

import PropTypes from 'prop-types';

import styles from '@styles/button.module.scss';

import Button from './Button';

const QuickActionButton = ({ action, onClick }) => {
  const isRejectAction = useMemo(() => action.action.toLowerCase().includes('reject'), [
    action.action,
  ]);

  return (
    <Button
      variant='secondary'
      className={styles.quickAction}
      color={isRejectAction ? 'danger' : 'success'}
      onClick={() => onClick(action)}
    >
      {action.label}
    </Button>
  );
};

QuickActionButton.propTypes = {
  action: PropTypes.shape({
    id: PropTypes.number,
    action: PropTypes.string,
    label: PropTypes.string,
  }),
  onClick: PropTypes.func,
};

QuickActionButton.defaultProps = {
  action: {
    action: '',
  },
  onClick: () => {},
};

export default memo(QuickActionButton);
