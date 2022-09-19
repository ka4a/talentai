import React, { memo } from 'react';

import PropTypes from 'prop-types';

const propTypes = {
  children: PropTypes.string,
  className: PropTypes.string,
  lineClassName: PropTypes.string,
};

const defaultProps = {
  children: '',
  className: '',
  lineClassName: '',
};

function MultilineText(props) {
  const { children, className, lineClassName } = props;

  return (
    <div className={className}>
      {children.split('\n').map((line, i) => (
        <div key={i} className={lineClassName}>
          {line}
        </div>
      ))}
    </div>
  );
}

MultilineText.propTypes = propTypes;
MultilineText.defaultProps = defaultProps;

export default memo(MultilineText);
