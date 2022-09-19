import { combineReducers } from 'redux';
import { persistReducer } from 'redux-persist';
import { createBrowserHistory } from 'history';
import { PURGE } from 'redux-persist/es/constants';
import { connectRouter } from 'connected-react-router';
import storage from 'redux-persist/lib/storage';

import user from './user';
import table from './table';
import modals from './modals';
import settings from './settings';

export const history = createBrowserHistory();

const appReducer = combineReducers({
  router: connectRouter(history),
  user,
  table,
  modals,
  settings,
});

const rootReducer = (state, action) => {
  if (action.type === PURGE) return appReducer(undefined, action);
  return appReducer(state, action);
};

const persistConfig = {
  storage,
  key: 'zookeep',
  blacklist: ['router', 'modals'],
};

export default persistReducer(persistConfig, rootReducer);
