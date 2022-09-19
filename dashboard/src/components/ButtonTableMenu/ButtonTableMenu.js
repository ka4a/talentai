import React, { memo } from 'react';
import { Button } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import styles from './ButtonTableMenu.module.scss';

ButtonTableMenu.propTypes = {
  className: PropTypes.string,
};

function ButtonTableMenu(props) {
  const { className, ...rest } = props;
  return (
    <Button
      className={classnames(styles.root, className, 'text-secondary')}
      {...rest}
    />
  );
}

export default memo(ButtonTableMenu);
