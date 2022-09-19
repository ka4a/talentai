import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import { ReactComponent as StarFilled } from '@images/icons/star-filled.svg';
import { ReactComponent as StarOutlined } from '@images/icons/star-outlined.svg';

import Typography from '../Typography';

import styles from './RatingInfo.module.scss';

const createArray = (length, value) => new Array(length ?? 0).fill(value);

const RatingInfo = ({ label, rating }) => {
  const filledStars = createArray(rating, true);
  const emptyStars = createArray(5 - rating, false);
  const stars = filledStars.concat(emptyStars);

  return (
    <div>
      <Typography
        variant='caption'
        className={classnames([styles.label, { [styles.noValue]: !rating }])}
      >
        {label}
      </Typography>

      {!rating && (
        <div>
          <Typography variant='caption'>-</Typography>
        </div>
      )}

      {Boolean(rating) && (
        <div className={styles.stars}>
          {stars.map((isFilledStar, idx) => {
            const Star = isFilledStar ? StarFilled : StarOutlined;
            return <Star key={idx} />;
          })}
        </div>
      )}
    </div>
  );
};

RatingInfo.propTypes = {
  label: PropTypes.string.isRequired,
  rating: PropTypes.number,
};

RatingInfo.defaultProps = {
  rating: null,
};

export default memo(RatingInfo);
