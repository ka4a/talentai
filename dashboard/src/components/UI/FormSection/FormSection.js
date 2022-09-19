import React, { memo } from 'react';

import classnames from 'classnames';
import PropTypes from 'prop-types';

import Typography from '../Typography';

import styles from './FormSection.module.scss';

function FormSection(props) {
  const { id, title, titleVariant, className, children, isLast, noBorder } = props;

  return (
    <div
      id={id}
      className={classnames(styles.section, className, {
        [styles.noBorder]: noBorder,
        [styles.isLast]: isLast,
      })}
    >
      {title && (
        <Typography className={styles[titleVariant]} variant={titleVariant}>
          {title}
        </Typography>
      )}
      {children}
    </div>
  );
}
FormSection.propTypes = {
  children: PropTypes.node.isRequired,
  title: PropTypes.string,
  titleVariant: PropTypes.string,
  isLast: PropTypes.bool,
  noBorder: PropTypes.bool,
  id: PropTypes.string,
};

FormSection.defaultProps = {
  title: null,
  titleVariant: 'h3',
  isLast: false,
  noBorder: false,
  id: undefined,
};

export default memo(FormSection);
