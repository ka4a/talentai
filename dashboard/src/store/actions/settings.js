export const CHANGE_LOCALE = 'CHANGE_LOCALE';
export const READ_LOCALE_DATA = 'READ_LOCALE_DATA';
export const READ_LOCALE_DATA_SUCCESS = 'READ_LOCALE_DATA_SUCCESS';

export const SET_COOKIE_USAGE_FLAG = 'SET_COOKIE_USAGE_FLAG';
export const SET_VERSION = 'SET_VERSION';

export const changeLocale = (locale) => ({
  type: CHANGE_LOCALE,
  payload: { locale },
});

export const readLocaleData = () => ({
  type: READ_LOCALE_DATA,
  swagger: {
    operationId: 'locale_data_read',
  },
});

export const setCookieUsageFlag = (flag) => ({
  type: SET_COOKIE_USAGE_FLAG,
  payload: { flag },
});

export const setVersion = (version) => ({
  type: SET_VERSION,
  payload: { version },
});

export const SET_PUBLIC_TABLE_PAGE_SIZE = 'SET_PUBLIC_TABLE_PAGE_SIZE';

export function setPublicTablePageSize(paginationKey, size) {
  return {
    type: SET_PUBLIC_TABLE_PAGE_SIZE,
    payload: { paginationKey, size },
  };
}
