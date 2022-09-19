import React from 'react';

import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { Typography } from '@components';

import styles from './Sections.module.scss';

const twoElementsStyles = classnames([
  styles.rowWrapper,
  styles.topGap,
  styles.twoElements,
]);

const NameSection = ({ FormInput }) => (
  <>
    <Typography variant='subheading'>
      <Trans>Name</Trans>
    </Typography>

    <div className={twoElementsStyles}>
      <FormInput name='firstName' label={t`First Name`} required />
      <FormInput name='lastName' label={t`Last Name(s)`} withoutCapitalize required />
    </div>

    <div className={twoElementsStyles}>
      <FormInput name='firstNameKanji' label={t`First Name (Kanji)`} />
      <FormInput name='lastNameKanji' label={t`Last Name (Kanji)`} />
    </div>

    <div className={twoElementsStyles}>
      <FormInput name='firstNameKatakana' label={t`First Name (Katakana)`} />
      <FormInput name='lastNameKatakana' label={t`Last Name (Katakana)`} />
    </div>

    <hr />
  </>
);

NameSection.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default NameSection;
