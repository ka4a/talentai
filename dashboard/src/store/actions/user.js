// SET
export const SET_USER = 'SET_USER';

export const setUser = (user) => ({
  type: SET_USER,
  payload: { user },
});

// READ
export const READ_USER = 'READ_USER';
export const READ_USER_SUCCESS = 'READ_USER_SUCCESS';
export const READ_USER_FAIL = 'READ_USER_FAIL';

export const readUser = () => ({
  type: READ_USER,
  swagger: {
    operationId: 'user_read_current',
  },
});

// LOGIN
export const LOGIN_USER = 'LOGIN_USER';
export const LOGIN_USER_SUCCESS = 'LOGIN_USER_SUCCESS';

export const loginUser = (email, password) => ({
  type: LOGIN_USER,
  swagger: {
    operationId: 'user_login',
    parameters: {
      data: {
        email,
        password,
      },
    },
  },
});

// LOGOUT
export const LOGOUT_USER = 'LOGOUT_USER';
export const LOGOUT_USER_SUCCESS = 'LOGOUT_USER_SUCCESS';

export const logoutUser = () => ({
  type: LOGOUT_USER,
  swagger: {
    operationId: 'user_logout',
  },
});

// UPDATE
export const UPDATE_USER = 'UPDATE_USER';
export const UPDATE_USER_SUCCESS = 'UPDATE_USER_SUCCESS';

const updateUserSwagger = (data) => ({
  operationId: 'user_update_settings',
  parameters: {
    data,
  },
});

export const updateUser = (data) => ({
  type: UPDATE_USER,
  swagger: updateUserSwagger(data),
});

// Update page handlers
export const UPDATE_USER_TABLE_PAGE_SIZE = 'UPDATE_USER_TABLE_PAGE_SIZE';
export const UPDATE_USER_TABLE_PAGE_SIZE_SUCCESS =
  'UPDATE_USER_TABLE_PAGE_SIZE_SUCCESS';

export function updateUserTablePageSize(paginationKey, size) {
  return {
    type: UPDATE_USER_TABLE_PAGE_SIZE,
    payload: { paginationKey, size },
    swagger: updateUserSwagger({
      frontendSettings: {
        [paginationKey]: size,
      },
    }),
  };
}

// AUTH
export const DEAUTHENTICATE_USER = 'DEAUTHENTICATE_USER';

export const deauthenticateUser = () => ({
  type: DEAUTHENTICATE_USER,
});
