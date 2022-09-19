import React, { useCallback } from 'react';
import { NavItem, NavLink } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';

const TabItem = (props) => {
  const { tabId, activeTabId, children, onSelect, show } = props;

  const handleClick = useCallback(() => onSelect(tabId), [tabId, onSelect]);

  if (!show) return null;

  return (
    <NavItem>
      <NavLink
        className={classnames({ active: activeTabId === tabId })}
        onClick={handleClick}
      >
        {children}
      </NavLink>
    </NavItem>
  );
};

TabItem.propTypes = {
  activeTabId: PropTypes.string,
  tabId: PropTypes.string.isRequired,
  onSelect: PropTypes.func.isRequired,
  show: PropTypes.bool,
};

TabItem.defaultProps = {
  show: true,
};

export default TabItem;
