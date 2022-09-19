import { client } from '@client';

export const onNotificationsAllChange = (newValue, user) => {
  const newState = { notificationSettings: [] };

  user.notificationSettings?.forEach(({ id, name }) => {
    newState.notificationSettings.push({ id, name, email: newValue });
  });

  return function () {
    this.setState((state) => ({ form: { ...state.form, ...newState } }));
  };
};

export const onFormSubmitDone = async (callback, obj, formState) => {
  const okFileFields = [];
  const failFileFields = [];

  const promises = [];

  if (formState.newPhoto !== null && !formState.newPhoto.uploaded) {
    promises.push(
      client
        .execute({
          operationId: 'user_upload_photo',
          parameters: {
            id: obj.id,
            file: formState.newPhoto.file,
          },
        })
        .then(() => {
          okFileFields.push('newPhoto');
          return true;
        })
        .catch(() => {
          failFileFields.push('newPhoto');
          return false;
        })
    );
  }

  const results = await Promise.all(promises);

  const statePatch = {};

  okFileFields.forEach((field) => {
    statePatch[field] = { ...formState[field], uploaded: true, error: false };
  });

  failFileFields.forEach((field) => {
    statePatch[field] = { ...formState[field], error: true };
  });

  callback(results.every(Boolean), statePatch);
};
