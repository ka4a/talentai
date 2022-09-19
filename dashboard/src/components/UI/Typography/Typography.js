import React from 'react';

import PropTypes from 'prop-types';
import classNames from 'classnames';

import styles from './Typography.module.scss';

const Typography = ({ children, variant, className, hasParsedMarkup, ...rest }) => {
  const TypographyTag = variant.startsWith('h') ? variant : 'div';

  return (
    <TypographyTag className={classNames([styles[variant], className])} {...rest}>
      {children}
    </TypographyTag>
  );
};

Typography.propTypes = {
  children: PropTypes.node,
  variant: PropTypes.oneOf([
    'jumbo',
    'h1',
    'h2',
    'h3',
    'subheading',
    'bodyStrong',
    'body',
    'button',
    'caption',
  ]),
  className: PropTypes.string,
  hasParsedMarkup: PropTypes.bool,
};

Typography.defaultProps = {
  hasParsedMarkup: false,
  variant: 'body',
  className: '',
  children: '',
};

export default Typography;
