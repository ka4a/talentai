import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useToggle } from 'react-use';
import { Dropdown as RSDropdown, DropdownToggle, DropdownMenu } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import styles from './Dropdown.module.scss';

const Dropdown = (props) => {
  const { selected, options, handleChange, trigger, isDisabled, variant } = props;

  const [isOpen, toggle] = useToggle(false);
  const [selectedValue, setSelectedValue] = useState({});

  const toggleDropdown = useCallback(
    (event) => {
      event.stopPropagation();
      toggle();
    },
    [toggle]
  );

  useEffect(() => {
    const option = options.find((option) => option.id === selected);
    if (option) setSelectedValue(option);
  }, [options, selected]);

  const handleSelectItem = useCallback(
    (event, option) => {
      toggleDropdown(event);
      setSelectedValue(option);
      handleChange(option);
    },
    [handleChange, toggleDropdown]
  );

  const triggerElement = useMemo(() => {
    if (trigger) return trigger;

    return (
      <>
        {selectedValue?.icon && (
          <span className={styles.icon}>{selectedValue.icon}</span>
        )}

        {selectedValue?.label}
      </>
    );
  }, [selectedValue.icon, selectedValue.label, trigger]);

  return (
    <RSDropdown
      isOpen={isOpen}
      toggle={toggleDropdown}
      className={trigger ? styles.transparentTrigger : styles.button}
      disabled={isDisabled}
    >
      <DropdownToggle
        className={classnames({ [styles.resetButtonStyles]: Boolean(trigger) })}
      >
        {triggerElement}
      </DropdownToggle>

      <DropdownMenu className={classnames(styles.menu, MENU_VARIANTS[variant])}>
        {options?.map((option) => (
          <div
            key={option.id}
            className={classnames(styles.option, {
              [styles.active]: option.id === selectedValue?.id,
            })}
            onClick={(event) => handleSelectItem(event, option)}
          >
            {option?.icon && <span className={styles.icon}>{option.icon}</span>}
            {option.label}
          </div>
        ))}
      </DropdownMenu>
    </RSDropdown>
  );
};

const MENU_VARIANTS = {
  default: '',
  overlapping: styles.overlapping,
};

const LocalPropTypes = {
  id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
};

Dropdown.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      id: LocalPropTypes.id,
      label: PropTypes.string,
    })
  ).isRequired,
  variant: PropTypes.oneOf(Object.keys(MENU_VARIANTS)),
  handleChange: PropTypes.func.isRequired,
  selected: LocalPropTypes.id.isRequired,
  trigger: PropTypes.node,
  isDisabled: PropTypes.bool,
};

Dropdown.defaultProps = {
  trigger: null,
  isDisabled: false,
  variant: 'default',
};

export default Dropdown;
