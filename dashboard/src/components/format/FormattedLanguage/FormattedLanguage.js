import React from 'react';

import PropTypes from 'prop-types';
import { useLingui } from '@lingui/react';

import { LANGUAGE_CHOICES, LANGUAGE_LEVEL_CHOICES } from '@constants';

import Typography from '../../UI/Typography';

import styles from './FormattedLanguage.module.scss';

const FormattedLanguage = ({ countryCode, level, type }) => {
  const { i18n } = useLingui();

  const { name } = LANGUAGE_CHOICES.find((el) => el.value === countryCode) ?? {};
  const countryName = name && i18n._(name);

  const formatLanguageLevel = (level) => {
    const name = LANGUAGE_LEVEL_CHOICES.find((el) => el.value === level)?.name;
    return name ? i18n._(name) : '';
  };

  return (
    <div>
      {type === 'withSubLevel' ? (
        <>
          <Typography variant='caption' className={styles.label}>
            {countryName}
          </Typography>

          <Typography variant='body' className={styles.subLabel}>
            {formatLanguageLevel(level)}
          </Typography>
        </>
      ) : (
        <Typography variant='caption' className={styles.value}>
          {formatLanguageLevel(level)}
        </Typography>
      )}
    </div>
  );
};

FormattedLanguage.propTypes = {
  countryCode: PropTypes.string,
  level: PropTypes.number,
  type: PropTypes.string,
};

export default FormattedLanguage;
