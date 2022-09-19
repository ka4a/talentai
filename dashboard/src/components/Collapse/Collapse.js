import React, { memo } from 'react';
import { Collapse as CollapseRS } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import CollapseArrowButton from '../UI/CollapseArrowButton';

import styles from './Collapse.module.scss';

const Collapse = ({ isOpen, toggle, title, isDisabled, children }) => (
  <div>
    <div
      onClick={isDisabled ? null : toggle}
      className={classnames([styles.header, { [styles.disabled]: isDisabled }])}
    >
      {title}

      <CollapseArrowButton isOpen={isOpen} isDisabled={isDisabled} />
    </div>

    <CollapseRS isOpen={isDisabled ? false : isOpen}>{children}</CollapseRS>
  </div>
);

Collapse.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  toggle: PropTypes.func.isRequired,
  title: PropTypes.node.isRequired,
  children: PropTypes.node.isRequired,
  isDisabled: PropTypes.bool,
};

Collapse.defaultProps = {
  isDisabled: false,
};

export default memo(Collapse);
