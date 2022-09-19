import React from 'react';

import { Trans } from '@lingui/macro';
import PropTypes from 'prop-types';

import { Typography } from '@components';
import { useLegalAgreementsList } from '@swrAPI';

import styles from './Sections.module.scss';

const Agreement = ({ FormInput }) => {
  const { privacyPolicyLink } = useLegalAgreementsList();

  return (
    <div className={styles.agreementWrapper}>
      <FormInput
        type='checkbox'
        name='isAgreed'
        label={
          <Typography>
            <Trans>I have read and agreed to the</Trans>{' '}
            <a
              href={privacyPolicyLink}
              target='_blank'
              rel='noreferrer'
              className={styles.link}
            >
              <Trans>Privacy Policies</Trans>
            </a>
          </Typography>
        }
      />
    </div>
  );
};

Agreement.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default Agreement;
