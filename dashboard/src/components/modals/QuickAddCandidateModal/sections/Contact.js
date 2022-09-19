import React from 'react';

import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { Typography } from '@components';

import styles from '../QuickAddCandidateModal.module.scss';

const Contact = ({ FormInput }) => (
  <>
    <Typography
      variant='subheading'
      className={classnames([styles.subtitle, styles.topGap])}
    >
      <Trans>Contact</Trans>
    </Typography>

    <div className={classnames([styles.rowWrapper, styles.twoElements])}>
      <FormInput name='email' label={t`Email (Primary)`} />
      <FormInput name='phone' label={t`Phone (Primary)`} />
    </div>
  </>
);

Contact.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default Contact;
