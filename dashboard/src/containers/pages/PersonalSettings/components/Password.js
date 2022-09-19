import React from 'react';

import classnames from 'classnames';
import PropTypes from 'prop-types';
import { t } from '@lingui/macro';

import { FormSection } from '@components';
import styles from '@styles/form.module.scss';

const Password = ({ FormInput }) => (
  <FormSection id='settings-password' title={t`Change password`}>
    <div className={classnames([styles.rowWrapper, styles.twoElementsNoAlign])}>
      <FormInput
        name='oldPassword'
        autoComplete='new-password'
        label={t`Current Password`}
        type='password-no-icon'
      />

      <FormInput name='newPassword' label={t`New Password`} type='password-no-icon' />
    </div>
  </FormSection>
);

Password.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default Password;
