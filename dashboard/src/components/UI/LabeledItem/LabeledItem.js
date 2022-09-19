import React, { memo, Fragment } from 'react';

import PropTypes from 'prop-types';
import parse from 'html-react-parser';
import classnames from 'classnames';

import Typography from '../Typography';

import styles from './LabeledItem.module.scss';

const LabeledItem = ({ label, value, variant, className, isLink, withCapitalize }) => {
  const isTextarea = variant === 'textarea';
  const isNumber = variant === 'number';

  const content = (() => {
    if (isTextarea) return value ? parse(value) : '-';
    else if (isNumber && typeof value === 'number') return String(value);
    else return value;
  })();

  const Wrapper = isLink ? 'a' : Fragment;
  const linkProps = { href: value, target: '_blank', rel: 'noopener noreferrer' };

  return (
    <div className={classnames([styles.wrapper, className])}>
      <Typography
        variant='caption'
        className={classnames([styles.label, { [styles.capitalize]: withCapitalize }])}
      >
        {label}
      </Typography>

      <Wrapper {...(isLink ? linkProps : {})}>
        <Typography
          variant='body'
          className={classnames(styles.value, {
            [styles.capitalize]: withCapitalize && !isTextarea,
            [styles.link]: isLink,
            [styles.textarea]: isTextarea,
          })}
          hasParsedMarkup={isTextarea}
        >
          {content || '-'}
        </Typography>
      </Wrapper>
    </div>
  );
};

LabeledItem.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number, PropTypes.node]),
  variant: PropTypes.oneOf(['text', 'textarea', 'number']),
  className: PropTypes.string,
  isLink: PropTypes.bool,
  withCapitalize: PropTypes.bool,
};

LabeledItem.defaultProps = {
  value: '',
  variant: 'text',
  className: '',
  isLink: false,
  withCapitalize: true,
};

export default memo(LabeledItem);
