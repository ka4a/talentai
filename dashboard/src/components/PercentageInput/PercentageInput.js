import React, { useState, useCallback } from 'react';
import { Input } from 'reactstrap';

import PropTypes from 'prop-types';

import { useForceUpdate, useDeferAfterUpdate } from '../../hooks';

const RE_PERCENT = /^((?:(?:1?\d{1,2})?(?:\.\d)?))?\.?%$/;

function setCursor(input, cursor) {
  input.selectionStart = cursor;
  input.selectionEnd = cursor;
}

function getPercentString(value) {
  let fixedPoint = (value * 100).toFixed(1);
  const removedEnding = '.0';
  if (fixedPoint.endsWith(removedEnding)) {
    const length = fixedPoint.length - removedEnding.length;
    fixedPoint = fixedPoint.substr(0, length);
  }

  return `${fixedPoint}%`;
}

function getPercentValue(valueStr) {
  let value = Number.parseFloat(valueStr);
  if (Number.isNaN(value)) value = 0;
  else if (value > 100) value = 100;
  else {
    value = Math.round(value * 10) / 10;
  }
  return (value / 100).toFixed(3);
}

PercentageInput.propTypes = {
  onChange: PropTypes.func,
  onBlur: PropTypes.func,
  id: PropTypes.number,
  name: PropTypes.string,
  invalid: PropTypes.bool,
};

export default function PercentageInput(props) {
  const { value, onChange, onBlur, id, name, invalid, ...rest } = props;
  const [text, setText] = useState(getPercentString(value));
  const forceUpdate = useForceUpdate();
  const deferAfterUpdate = useDeferAfterUpdate();

  const handleChange = useCallback(
    (event) => {
      const newText = event.target.value;
      const match = newText.match(RE_PERCENT);

      if (match) {
        setText(newText);
        if (onChange) {
          onChange({
            target: {
              name,
              value: getPercentValue(match[1]),
            },
          });
        }
        return;
      }
      const curCursor = event.target.selectionStart;
      const input = event.target;

      // To make sure cursor stays there it was if update is failed
      deferAfterUpdate(() => {
        let cursor = curCursor;
        if (newText.length > text.length) cursor--;
        if (newText.length < text.length) cursor++;
        setCursor(input, cursor);
      });

      forceUpdate();
    },
    [setText, text, forceUpdate, deferAfterUpdate, onChange, name]
  );

  const handleBlur = useCallback(
    (event) => {
      setText(getPercentString(value));
      if (onBlur) onBlur(event);
    },
    [onBlur, value]
  );

  return (
    <Input
      id={id}
      name={name}
      value={text}
      invalid={invalid}
      bsSize='lg'
      onChange={handleChange}
      onBlur={handleBlur}
      {...rest}
    />
  );
}
