import React, { memo } from 'react';
import Rating from 'react-rating';
import { ImCross } from 'react-icons/im';

import classnames from 'classnames';
import PropTypes from 'prop-types';

import { Typography } from '@components';
import { ReactComponent as StarFilled } from '@images/icons/star-filled.svg';
import { ReactComponent as StarOutlined } from '@images/icons/star-outlined.svg';

import styles from './RatingInput.module.scss';

const RatingInput = ({ value, label, onChange, required, isDisabled, resetRating }) => (
  <div
    className={classnames(styles.wrapper, {
      [styles.disabled]: isDisabled,
    })}
  >
    <label className={styles.label}>
      <Typography variant='caption'>
        {label}
        {required && <span className={styles.required}>*</span>}
      </Typography>
    </label>

    <div className={styles.input}>
      <Rating
        initialRating={value}
        onChange={onChange}
        fullSymbol={<StarFilled className={styles.star} />}
        emptySymbol={<StarOutlined className={styles.star} />}
      />

      {Boolean(value) && <ImCross className={styles.cross} onClick={resetRating} />}
    </div>
  </div>
);

RatingInput.propTypes = {
  value: PropTypes.number.isRequired,
  label: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  resetRating: PropTypes.func.isRequired,
  required: PropTypes.bool,
  isDisabled: PropTypes.bool,
};

RatingInput.defaultProps = {
  required: false,
  isDisabled: false,
};

export default memo(RatingInput);
