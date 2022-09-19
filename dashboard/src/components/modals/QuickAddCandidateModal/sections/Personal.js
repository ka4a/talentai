import React from 'react';

import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { Typography } from '@components';

import styles from '../QuickAddCandidateModal.module.scss';

const Personal = ({ FormInput }) => (
  <>
    <Typography variant='subheading' className={styles.subtitle}>
      <Trans>Personal</Trans>
    </Typography>

    <div className={classnames([styles.rowWrapper, styles.twoElements])}>
      <FormInput name='firstName' label={t`First Name`} required />
      <FormInput name='lastName' label={t`Last Name`} required />
    </div>

    <div className={classnames([styles.rowWrapper, styles.twoElements, styles.topGap])}>
      <FormInput name='firstNameKanji' label={t`First Name (Kanji)`} />
      <FormInput name='lastNameKanji' label={t`Last Name (Kanji)`} />
    </div>
  </>
);

Personal.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default Personal;
