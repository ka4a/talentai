import React from 'react';
import { Provider } from 'react-redux';

import configureStore from 'redux-mock-store';
import { I18nProvider } from '@lingui/react';
import { render as rtlRender } from '@testing-library/react';

import initialStore from '@tests/__mocks__/store';

import i18n from '../i18n';

export * from '@testing-library/react';

export const render = (ui, renderOptions = {}) => {
  const Wrapper = ({ children }) => (
    <Provider store={configureStore()(initialStore)}>
      <I18nProvider i18n={i18n}>{children}</I18nProvider>
    </Provider>
  );

  return rtlRender(ui, { wrapper: Wrapper, ...renderOptions });
};
