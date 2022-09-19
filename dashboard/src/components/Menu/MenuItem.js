import React, { memo } from 'react';
import { NavItem } from 'reactstrap';
import { Link } from 'react-router-dom';
import { useLocation } from 'react-router-dom';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { Trans } from '@lingui/macro';

import Typography from '../UI/Typography';

import styles from './Menu.module.scss';

const MenuItem = (props) => {
  const location = useLocation();
  const { title, link, icon, isDisabled, regex } = props;

  // check regex to match subpages, e.g. /jobs or /job/1
  const isActive = regex ? regex.test(location.pathname) : location.pathname === link;

  return (
    <NavItem>
      <Link
        to={link}
        className={classnames(styles.item, {
          [styles.active]: isActive,
          [styles.disabled]: isDisabled,
        })}
      >
        {icon}
        <Typography variant='button'>
          <Trans>{title}</Trans>
        </Typography>
      </Link>
    </NavItem>
  );
};

MenuItem.propTypes = {
  title: PropTypes.string.isRequired,
  link: PropTypes.string.isRequired,
  icon: PropTypes.element.isRequired,
  isDisabled: PropTypes.bool,
  regex: PropTypes.shape({}),
};

MenuItem.defaultProps = {
  isDisabled: false,
  regex: null,
};

export default memo(MenuItem);
