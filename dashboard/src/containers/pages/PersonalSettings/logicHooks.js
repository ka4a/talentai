import React, { useCallback } from 'react';
import { useHistory } from 'react-router-dom';

import { Trans } from '@lingui/macro';

import { ButtonBar, Typography } from '@components';
import styles from '@styles/form.module.scss';

import Details from './components/Details';
import Password from './components/Password';
import Notifications from './components/Notifications';

const useGetElements = () => {
  const history = useHistory();

  const renderHeader = useCallback(
    () => (
      <Typography variant='h1' className={styles.title}>
        <Trans>Personal Settings</Trans>
      </Typography>
    ),
    []
  );

  const renderInputs = useCallback(
    ({ FormInput, setValue, form, errors }) => (
      <>
        <Details
          FormInput={FormInput}
          setValue={setValue}
          form={form}
          errors={errors}
        />
        <Password FormInput={FormInput} />
        <Notifications FormInput={FormInput} />
      </>
    ),
    []
  );

  const renderButtons = useCallback(
    (form, makeOnSubmit, { disabled }) => (
      <ButtonBar
        onCancel={history.goBack}
        onSave={makeOnSubmit({ published: true })}
        isDisabled={disabled}
      />
    ),
    [history]
  );

  return {
    header: renderHeader,
    inputs: renderInputs,
    buttons: renderButtons,
  };
};

export { useGetElements };
