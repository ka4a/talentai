import React from 'react';

import { Trans } from '@lingui/macro';

import { closeAlert as closeAlertAction, openAlert as openAlertAction } from '@actions';
import Button from '@components/UI/Button';

import store from '../store';

// Buttons presets
export const getAlertButtons = (resolve) => (
  <Button onClick={resolve}>
    <Trans>Close</Trans>
  </Button>
);

export const getConfirmButtons = (resolve, reject) => (
  <>
    <Button onClick={reject} variant='secondary' color='neutral'>
      <Trans>Cancel</Trans>
    </Button>

    <Button onClick={resolve}>
      <Trans>Yes</Trans>
    </Button>
  </>
);

export const getMissingInformationButtons = (resolve, reject) => (
  <>
    <Button onClick={resolve} variant='secondary' color='danger'>
      <Trans>Save Anyway</Trans>
    </Button>

    <Button onClick={reject} variant='secondary'>
      <Trans>Continue Editing</Trans>
    </Button>
  </>
);

// Main promisified opening function
export const openDialog = ({ title, description, content, getButtons }) => {
  const action = openAlertAction(title, description, content, getButtons);

  action.payload.promise = new Promise((resolve, reject) => {
    action.payload.resolve = resolve;
    action.payload.reject = reject;
  });

  const close = () => {
    store.dispatch(closeAlertAction(action.payload.id));
  };
  action.payload.promise.then(close, close);

  store.dispatch(action);

  return action.payload.promise;
};

// Opening functions with buttons presets
const makeOpenDialog = (getButtons) => ({ title, description, content }) =>
  openDialog({ title, description, content, getButtons });

export const openAlert = makeOpenDialog(getAlertButtons);
export const openConfirm = makeOpenDialog(getConfirmButtons);
export const openMissingInformation = makeOpenDialog(getMissingInformationButtons);
