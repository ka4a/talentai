import React, { memo, useCallback } from 'react';
import { Dropdown, DropdownMenu, DropdownToggle } from 'reactstrap';
import { useToggle } from 'react-use';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

const SimpleDropdown = (props) => {
  const { className, menuClassname, buttonClassname, trigger, children } = props;

  const [isOpen, toggle] = useToggle(false);

  const toggleDropdown = useCallback(
    (event) => {
      event.stopPropagation();
      toggle();
    },
    [toggle]
  );

  return (
    <Dropdown
      isOpen={isOpen}
      className={className}
      toggle={toggleDropdown}
      direction='down'
    >
      <DropdownToggle className={buttonClassname}>{trigger}</DropdownToggle>

      <DropdownMenu className={menuClassname} right>
        {children}
      </DropdownMenu>
    </Dropdown>
  );
};

SimpleDropdown.propTypes = {
  className: PropTypes.string,
  menuClassname: PropTypes.string,
  buttonClassname: PropTypes.string,
  trigger: PropTypes.node.isRequired,
  children: PropTypes.node.isRequired,
};

SimpleDropdown.defaultProps = {
  className: '',
  menuClassname: '',
  buttonClassname: '',
  trigger: t`Show`,
};

export default memo(SimpleDropdown);
