import React, { createContext, useContext } from 'react';

import startsWith from 'lodash/startsWith';
import { t, defineMessage } from '@lingui/macro';
import has from 'lodash/has';

import { openAlert } from '@utils/alert';
import { showErrorToast } from '@utils/common';

const FETCH_ERROR_TEXT_PLACEHOLDER = t`An error occurred, please try again later`;

const ERROR_METHOD_VERB = {
  get: 'load',
  post: 'create',
  patch: 'change',
  put: 'change',
  delete: 'delete',
};

const getResponseOrThrowCustomError = (error) => {
  const response = error?.response;

  if (!response) {
    window.dispatchEvent(new CustomEvent('custom-error', { detail: error }));
    throw error;
  }

  return response;
};

export const getErrorTextFromFetchError = (
  error,
  placeholder = FETCH_ERROR_TEXT_PLACEHOLDER
) => {
  if (has(error, 'response.obj.detail')) {
    return error.response.obj.detail;
  } else if (has(error, 'response.obj.nonFieldErrors')) {
    return error.response.obj.nonFieldErrors.join('\n');
  } else if (has(error, 'response')) {
    if (startsWith(error.response.status, '5')) {
      // don't show server errors
      return placeholder;
    }
    return `(${error.response.status}) ${error.response.statusText}`;
  }

  console.error(error);

  return placeholder;
};

export const fetchErrorHandler = (error) => {
  /* Preferably should be used only in response to user actions */
  const { url } = getResponseOrThrowCustomError(error);

  const text = getErrorTextFromFetchError(error);

  // case is handled elsewhere so we ignore here
  if (error?.response.headers?.['x-authenticated'] === 'NOT_AUTHENTICATED') return;

  showErrorToast(
    <div>
      <div>{text ? text : t`Error on endpoint ${url}`}</div>
    </div>
  );
};

export const handleRequestError = (error, method) => {
  const { url } = getResponseOrThrowCustomError(error);
  const text = getErrorTextFromFetchError(error);

  const verb = ERROR_METHOD_VERB[method];

  let description = verb ? `Failed to ${verb}` : 'Request failed';
  description = url ? `${description} ${url}` : `${description}`;

  return openAlert({
    title: t`Error`,
    content: (
      <>
        <div key='description'>{description}:</div>
        <div key='text'>{text}</div>
      </>
    ),
  });
};

export class ZendeskError extends Error {
  isNonBlocking = true;
  toast = {
    title: defineMessage({ message: 'Something went wrong with Zendesk.' }).id,
  };
}

export const ErrorBoundaryContext = createContext({
  reportError(error, info) {},
});

export const useReportError = () => {
  const context = useContext(ErrorBoundaryContext);
  return context.reportError;
};
