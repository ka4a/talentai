import React, { memo } from 'react';

import PropTypes from 'prop-types';

const stopPropagation = (e) => {
  e.stopPropagation();
};

const EventIsolator = (props) => {
  const { children, click, mouseOver, mouseOut } = props;

  return (
    <div
      onClick={click ? stopPropagation : null}
      onMouseOver={mouseOver ? stopPropagation : null}
      onMouseOut={mouseOut ? stopPropagation : null}
    >
      {children}
    </div>
  );
};

EventIsolator.propTypes = {
  click: PropTypes.bool,
  mouseOver: PropTypes.bool,
  mouseOut: PropTypes.bool,
};

export default memo(EventIsolator);
