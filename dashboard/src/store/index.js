import { applyMiddleware, createStore } from 'redux';
import { composeWithDevTools } from 'redux-devtools-extension/developmentOnly';
import { routerMiddleware } from 'connected-react-router';
import { persistStore } from 'redux-persist';

import { setVersion } from '@actions';
import { getRelease } from '@utils/common';
import { swaggerClientMiddleware } from '@client';
import { storeVersion as currentVersion } from '@config';

import rootReducer, { history } from './reducers';

const store = createStore(
  rootReducer,
  composeWithDevTools(
    applyMiddleware(routerMiddleware(history), swaggerClientMiddleware)
  )
);

export const persistor = persistStore(store, null, async () => {
  const { version: prevVersion, release: prevRelease } =
    store.getState()?.settings ?? {};
  const currentRelease = getRelease();

  if (prevVersion !== currentVersion || prevRelease !== currentRelease) {
    await persistor.purge();
    store.dispatch(setVersion(currentVersion));
  }
});

export default store;
