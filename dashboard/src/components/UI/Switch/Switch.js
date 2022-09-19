import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import Typography from '@components/UI/Typography';

import styles from './Switch.module.scss';

const Switch = ({ label, checked, onChange, disabled, wrapperClassName }) => {
  const onClick = disabled ? null : () => onChange(!checked);

  const checkedStyle = { [styles.checked]: checked, [styles.disabled]: disabled };

  return (
    <div className={classnames(styles.wrapper, wrapperClassName)}>
      <div onClick={onClick} className={classnames(styles.switch, checkedStyle)}>
        <div className={classnames([styles.circle, checkedStyle])} />
      </div>

      {label && (
        <Typography onClick={onClick} variant='caption' className={styles.label}>
          {label}
        </Typography>
      )}
    </div>
  );
};

Switch.propTypes = {
  wrapperClassName: PropTypes.string,
  label: PropTypes.string.isRequired,
  checked: PropTypes.bool.isRequired,
  disabled: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
};

Switch.defaultProps = {
  disabled: false,
  wrapperClassName: '',
};

export default memo(Switch);
