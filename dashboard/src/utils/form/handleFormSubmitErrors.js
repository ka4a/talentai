import { omit } from 'lodash';

import { getErrorTextFromFetchError, showErrorToast } from '@utils';

import { SUBMISSION_ERROR } from '../../constants/errorHandling';

export default function handleFormSubmitErrors(error, i18n) {
  let fieldErrors = null;

  const { response } = error;
  let message = i18n._(SUBMISSION_ERROR);

  if (response?.status === 400) {
    fieldErrors = omit(response.obj, 'detail', 'nonFieldErrors');
  } else {
    message = getErrorTextFromFetchError(error, message);
  }

  showErrorToast(message);

  return { fieldErrors };
}
