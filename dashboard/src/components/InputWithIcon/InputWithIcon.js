import React from 'react';
import { Input } from 'reactstrap';

import classnames from 'classnames';
import PropTypes from 'prop-types';

import styles from './InputWithIcon.module.scss';

export default function InputWithIcon(props) {
  const { className, Icon, onIconClick, iconActive, iconAttrs, align, ...rest } = props;

  return (
    <div className={classnames(styles.container, className)}>
      <Input {...rest} />
      <div className={classnames(styles.addon, styles[align])}>
        <div className={styles.iconContainer}>
          {Icon ? (
            <Icon
              className={classnames({ [styles.active]: iconActive })}
              onClick={onIconClick}
              {...iconAttrs}
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}

InputWithIcon.propTypes = {
  align: PropTypes.oneOf(['left', 'right']),
  Icon: PropTypes.node.isRequired,
  iconAttrs: PropTypes.shape({
    size: PropTypes.number,
  }),
  onIconClick: PropTypes.func,
  iconActive: PropTypes.bool,
};

InputWithIcon.defaultProps = {
  align: 'right',
  iconActive: false,
};
