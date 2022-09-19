import React, { useCallback } from 'react';
import { useHistory } from 'react-router';

import PropTypes from 'prop-types';
import { useLingui } from '@lingui/react';

import { useStaffRead } from '@swrAPI';
import {
  FormContextProvider,
  ReqStatus,
  SectionsMenu,
  WindowBackground,
} from '@components';
import { client } from '@client';
import { handleFormSubmitErrors, validateOnBackend } from '@utils';

import UserForm from './components/UserForm';
import { USER_EDIT_SECTIONS } from './constants';

import styles from './UserEditPage.module.scss';

function UserEditPage({ match }) {
  const { userId } = match.params;

  const userSWR = useStaffRead(userId);
  const { loading, mutate, error } = userSWR;
  const user = userId ? userSWR.data : BLANK_FORM;

  const isCreate = userId == null;

  const handleSubmit = useSubmitForm(userId, mutate);

  const handleValidate = useCallback(
    (form) => validateOnBackend('staff_validate_partial_update', form, userId),
    [userId]
  );

  return (
    <div className={styles.wrapper}>
      <WindowBackground className={styles.formContainer}>
        {userId && !user ? (
          <ReqStatus loading={loading} error={error} />
        ) : (
          <FormContextProvider
            initialForm={user}
            onSubmit={handleSubmit}
            onValidate={handleValidate}
          >
            <UserForm isCreate={isCreate} />
          </FormContextProvider>
        )}
      </WindowBackground>
      <SectionsMenu sections={USER_EDIT_SECTIONS} />
    </div>
  );
}

UserEditPage.propTypes = {
  match: PropTypes.shape({
    params: PropTypes.shape({
      userId: PropTypes.string,
    }),
  }).isRequired,
};

const BLANK_FORM = {
  photo: null,
  newPhoto: null,
};

function useSubmitForm(userId, mutate) {
  const history = useHistory();
  const { i18n } = useLingui();

  return useCallback(
    async (form) => {
      try {
        await submitForm('staff_partial_update', userId, form);
      } catch (error) {
        return handleFormSubmitErrors(error, i18n);
      }

      const newPhoto = await uploadFile('staff_upload_photo', userId, form.newPhoto);
      const formUpdates = { newPhoto };

      if (newPhoto?.error) {
        return { ...handleFormSubmitErrors(newPhoto.error, i18n), formUpdates };
      }

      // Setting initial state
      mutate({ ...form, ...formUpdates });
      history.goBack();

      return { formUpdates };
    },
    [i18n, userId, history, mutate]
  );
}

async function uploadFile(operationId, id, fileField) {
  if (!fileField || fileField.uploaded) return fileField;

  try {
    await client.execute({
      operationId,
      parameters: { id, file: fileField.file },
    });
    return { ...fileField, uploaded: true };
  } catch (error) {
    return { ...fileField, error };
  }
}

function submitForm(operationId, id, data) {
  return client.execute({
    operationId,
    parameters: { id, data },
  });
}

export default UserEditPage;
