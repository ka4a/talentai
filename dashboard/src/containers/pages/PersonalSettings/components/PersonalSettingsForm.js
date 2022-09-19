import React, { memo, useCallback, useMemo } from 'react';
import { useSelector, useDispatch, batch } from 'react-redux';

import { SwaggerForm, WindowBackground } from '@components';
import { changeLocale, readUser } from '@actions';
import styles from '@styles/form.module.scss';

import { initialState } from '../constants';
import { useGetElements } from '../logicHooks';
import { onNotificationsAllChange, onFormSubmitDone } from '../handlers';

const PersonalSettingsForm = () => {
  const user = useSelector((state) => state.user);

  const dispatch = useDispatch();

  const onSaved = (user) => {
    batch(() => {
      dispatch(changeLocale(user.locale));
      dispatch(readUser());
    });
  };

  const { header, inputs, buttons } = useGetElements();

  const stateBoundHandlers = useMemo(
    () => ({
      onNotificationsDisable: onNotificationsAllChange(false, user),
      onNotificationsEnable: onNotificationsAllChange(true, user),
    }),
    [user]
  );

  const processFormState = useCallback(
    (form) => ({
      ...form,
      newPhoto: null,
    }),
    []
  );

  return (
    <WindowBackground className={styles.formContainer}>
      <SwaggerForm
        editing
        formId='personalSettingsForm'
        // endpoints
        readOperationId='user_read_current'
        operationId='user_update_settings'
        // form processing
        onSaved={onSaved}
        initialState={initialState}
        processFormState={processFormState}
        onFormSubmitDone={onFormSubmitDone}
        handlers={stateBoundHandlers}
        resetAfterSave
        // render elements
        formTop={header}
        inputs={inputs}
        buttons={buttons}
      />
    </WindowBackground>
  );
};

export default memo(PersonalSettingsForm);
