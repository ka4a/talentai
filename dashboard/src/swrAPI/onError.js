import { DEAUTHENTICATE_USER } from '@actions';

import store from '../store';
import openSessionExpiredDialog from './openSessionExpiredDialog';

const onError = (error) => {
  if (error?.response.headers?.['x-authenticated'] === 'NOT_AUTHENTICATED') {
    store.dispatch({ type: DEAUTHENTICATE_USER });
    openSessionExpiredDialog();
  }
};

export default onError;
