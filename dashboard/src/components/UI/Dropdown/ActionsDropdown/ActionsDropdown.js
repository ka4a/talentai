import React, { memo, useCallback } from 'react';
import { useToggle } from 'react-use';
import { BsThreeDots } from 'react-icons/bs';
import { Dropdown, DropdownToggle, DropdownMenu } from 'reactstrap';

import PropTypes from 'prop-types';

import Action from './Action';

import styles from './ActionsDropdown.module.scss';

const ActionsDropdown = ({ button, actions }) => {
  const [isOpen, toggle] = useToggle(false);

  const stopPropagation = useCallback((event) => {
    event.stopPropagation();
  }, []);

  return (
    <Dropdown isOpen={isOpen} toggle={toggle}>
      <DropdownToggle className={styles.actionButton} onClick={stopPropagation}>
        {button}
      </DropdownToggle>

      <DropdownMenu className={styles.actionsMenu}>
        {actions.map((action) => (
          <Action
            toggleDropdown={toggle}
            key={action.transKey ?? action.text}
            {...action}
          />
        ))}
      </DropdownMenu>
    </Dropdown>
  );
};

ActionsDropdown.propTypes = {
  actions: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string,
      transKey: PropTypes.string, // i18n id of translated string
      text: PropTypes.string,
      handler: PropTypes.func,
    })
  ).isRequired,
  button: PropTypes.element,
};

ActionsDropdown.defaultProps = {
  button: <BsThreeDots size={24} />,
};

export default memo(ActionsDropdown);
