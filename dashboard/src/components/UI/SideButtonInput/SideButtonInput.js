import React, { useCallback, useRef } from 'react';
import { Input, InputGroup, InputGroupAddon, Button } from 'reactstrap';

import classNames from 'classnames';
import PropTypes from 'prop-types';

import buttonStyles from '@styles/button.module.scss';

import styles from './SideButtonInput.module.scss';

function SideButtonInput(props) {
  const {
    buttonSide,
    onButtonClick,
    onChange,
    value,
    isReadOnly,
    buttonVariant,
    buttonColor,
    buttonText,
  } = props;

  const inputRef = useRef();

  let handleButtonClick = useCallback(
    (event) => {
      const inputElement = inputRef.current;
      onButtonClick(event, inputElement?.value);
    },
    [onButtonClick]
  );

  if (!onButtonClick) handleButtonClick = null;

  const buttonClassName = classNames(
    buttonStyles.button,
    buttonStyles[buttonVariant],
    buttonStyles[buttonColor]
  );

  return (
    <InputGroup>
      <Input
        className={styles.input}
        readOnly={isReadOnly}
        value={value}
        onChange={onChange}
        innerRef={inputRef}
      />
      <InputGroupAddon addonType={buttonSide}>
        <Button className={buttonClassName} onClick={handleButtonClick}>
          {buttonText}
        </Button>
      </InputGroupAddon>
    </InputGroup>
  );
}

SideButtonInput.propTypes = {
  value: PropTypes.string,
  onChange: PropTypes.func,
  onButtonClick: PropTypes.func,
  buttonSide: PropTypes.oneOf(['append', 'prepend']),
  isReadOnly: PropTypes.bool,
  buttonVariant: PropTypes.oneOf(['primary', 'secondary', 'text', 'dot']),
  buttonColor: PropTypes.oneOf(['success', 'danger', 'neutral', 'inverse', '']),
  buttonText: PropTypes.node.isRequired,
};

SideButtonInput.defaultProps = {
  value: '',
  onChange: null,
  onButtonClick: null,
  buttonSide: 'append',
  isReadOnly: false,
  buttonVariant: 'primary',
  buttonColor: '',
};

export default SideButtonInput;
