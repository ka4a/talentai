import { getRelease } from '@utils';
import {
  CHANGE_LOCALE,
  READ_LOCALE_DATA_SUCCESS,
  SET_COOKIE_USAGE_FLAG,
  LOGIN_USER_SUCCESS,
  READ_USER_SUCCESS,
  SET_VERSION,
  SET_USER,
  SET_PUBLIC_TABLE_PAGE_SIZE,
} from '@actions';

import createReducer from '../createReducer';

const initialState = {
  locale: null,
  localeData: {},
  cookieUsage: false,
  release: getRelease(),
  version: null,
  publicTablePageSize: {
    careerSiteJobPostingsShowPer: 25,
  },
};

const handleLogin = (state, payload) => ({
  ...state,
  locale: payload.locale ?? state.locale,
  cookieUsage: true,
});

const actionHandlers = {
  // locale
  [CHANGE_LOCALE]: (state, payload) => ({ ...state, locale: payload.locale }),
  [SET_USER]: (state, payload) => ({
    ...state,
    locale: payload.user?.locale ?? state.locale,
  }),
  [SET_PUBLIC_TABLE_PAGE_SIZE]: (state, { paginationKey, size }) => ({
    ...state,
    publicTablePageSize: {
      ...state.publicTablePageSize,
      [paginationKey]: size,
    },
  }),
  [READ_USER_SUCCESS]: handleLogin,
  [LOGIN_USER_SUCCESS]: handleLogin,
  [READ_LOCALE_DATA_SUCCESS]: (state, payload) => ({ ...state, localeData: payload }),
  // cookie usage
  [SET_COOKIE_USAGE_FLAG]: (state, payload) => ({
    ...state,
    cookieUsage: payload.flag,
  }),
  [SET_VERSION]: (state, payload) => ({ ...state, version: payload.version }),
};

export default createReducer(initialState, actionHandlers);
