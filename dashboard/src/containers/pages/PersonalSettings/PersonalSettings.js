import React, { memo } from 'react';

import { t } from '@lingui/macro';

import { SectionsMenu, DefaultPageContainer } from '@components';
import styles from '@styles/form.module.scss';

import PersonalSettingsForm from './components/PersonalSettingsForm';
import { SECTIONS } from './constants';

const PersonalSettings = () => (
  <DefaultPageContainer title={t`Personal Settings`}>
    <div className={styles.wrapper}>
      <PersonalSettingsForm />
      <SectionsMenu sections={SECTIONS} />
    </div>
  </DefaultPageContainer>
);

export default memo(PersonalSettings);
