import React from 'react';
import { HiLocationMarker } from 'react-icons/hi';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { Trans } from '@lingui/macro';

import { Typography } from '@components';
import { formatNumber } from '@utils';

import styles from './CandidateInfoRow.module.scss';

function CandidateInfoRow(props) {
  const { position, city, prefecture, currency, salary } = props;

  const location = city && prefecture ? `${city}, ${prefecture}` : city;

  return (
    <div className={styles.root}>
      {position && (
        <Typography className={styles.subInfo} variant='bodyStrong'>
          {position}
        </Typography>
      )}

      {city && (
        <div className={classnames(styles.location, styles.subInfo)}>
          <HiLocationMarker />
          <Typography variant='bodyStrong'>{location}</Typography>
        </div>
      )}

      {Boolean(salary && salary !== '0') && (
        <div className={styles.salary}>
          <Typography variant='button'>
            <Trans>{formatNumber({ value: salary, currency })} / year</Trans>
          </Typography>
        </div>
      )}
    </div>
  );
}

CandidateInfoRow.propTypes = {
  position: PropTypes.string,
  city: PropTypes.string,
  prefecture: PropTypes.string,
  salary: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  currency: PropTypes.string,
};

export default CandidateInfoRow;
