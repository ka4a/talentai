import * as Sentry from '@sentry/react';
import Swagger from 'swagger-client';
import Cookies from 'js-cookie';

import { DEAUTHENTICATE_USER } from '@actions';
import openSessionExpiredDialog from '@swrAPI/openSessionExpiredDialog';

import store from './store';

const csrfExcludeMethods = ['GET', 'HEAD', 'OPTIONS', 'TRACE'];

const csrfRequestInterceptor = (req) => {
  if (!csrfExcludeMethods.includes(req.method)) {
    req.headers['X-CSRFToken'] = Cookies.get('csrftoken');
  }

  return req;
};

const xAuthResponseInterceptor = (res) => {
  const x_authenticated = res.headers?.['x-authenticated'];

  if (x_authenticated === 'NOT_AUTHENTICATED' && res.status === 403) {
    store.dispatch({ type: DEAUTHENTICATE_USER });
    openSessionExpiredDialog();
  }

  return res;
};

/**
 * If 'client' is not initialized, 'waitingClient' will replace it
 * and keep all outgoing requests to the 'waitingRequests' list.
 * After 'client' is initialized, it processes all requests from this list
 */
const waitingRequests = [];
const waitingClient = {
  execute(...executeArguments) {
    return new Promise((resolve, reject) => {
      waitingRequests.push({ executeArguments, resolve, reject });
    });
  },
};

export let client = waitingClient;

export function fetchSwagger() {
  let swagger_specs = null;

  try {
    swagger_specs = require('./swagger_specs.json');
  } catch (_) {
    console.warn('Swagger Specifications missing, they will be loaded from API.');
  }

  return new Promise((resolve, reject) => {
    const isClientInitialized = client !== null && client !== waitingClient;
    if (isClientInitialized) resolve();

    Swagger({ url: '/swagger.json', spec: swagger_specs })
      .then((newClient) => {
        newClient.spec.host = window.location.host; // fix for dev server host

        // hacky way to add global csrf request interceptor
        const origHttp = newClient.http;
        newClient.http = async function (url, request = {}) {
          if (typeof url === 'object') {
            url.requestInterceptor = csrfRequestInterceptor;
            url.responseInterceptor = xAuthResponseInterceptor;
          } else {
            request.requestInterceptor = csrfRequestInterceptor;
            request.responseInterceptor = xAuthResponseInterceptor;
          }

          return origHttp(url, request);
        };

        client = newClient;

        // process all waiting requests if there are any and clean the array
        waitingRequests.splice(0).forEach(({ executeArguments, resolve, reject }) => {
          client
            .execute(...executeArguments)
            .then(resolve)
            .catch(reject);
        });

        resolve();
      })
      .catch((error) => {
        waitingRequests.splice(0).forEach(({ reject }) => reject(error));

        reject(error);
      });
  });
}

export const swaggerClientMiddleware = (store) => (next) => (action) => {
  if (!action.swagger) return next(action);

  next(action);

  return new Promise((resolve, reject) => {
    const meta = { previousAction: action };

    client
      .execute(action.swagger)
      .then((response) => {
        store.dispatch({
          type: `${action.type}_SUCCESS`,
          payload: response.obj,
          meta,
        });

        resolve(response);
      })
      .catch((error) => {
        store.dispatch({
          type: `${action.type}_FAIL`,
          payload: { error },
          meta,
        });

        // temp block for capture issue with CSRF token
        // we don't want to log every failed backend response
        if (
          error.message.toLowerCase().includes('csrf') &&
          process.env.NODE_ENV === 'production'
        ) {
          Sentry.captureException(error);
        }

        reject(error);
      });
  });
};
