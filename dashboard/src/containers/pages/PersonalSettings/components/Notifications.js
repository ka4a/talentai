import React from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';

import { FormSection } from '@components';

import styles from '../PersonalSettings.module.scss';

const Notifications = ({ FormInput }) => {
  const notificationSettings = useSelector((state) => state.user.notificationSettings);

  return (
    <FormSection id='settings-notifications' title={t`Email Notifications`}>
      <div className={styles.notificationsWrapper}>
        {notificationSettings.map(({ name, description }, index) => (
          <FormInput
            key={name}
            type='checkbox'
            name={`notificationSettings[${index}].email`}
            label={description}
          />
        ))}
      </div>
    </FormSection>
  );
};

Notifications.propTypes = {
  FormInput: PropTypes.func.isRequired,
};

export default Notifications;
