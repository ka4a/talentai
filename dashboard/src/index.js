import 'react-datepicker/dist/react-datepicker.css';
import './styles/bootstrap-custom.scss';
import './styles/toastify-custom.scss';
import './styles/style.scss';
import './styles/fonts.scss';

import React from 'react';
import ReactDOM from 'react-dom';
import { pdfjs } from 'react-pdf';
import { Provider } from 'react-redux';
import { registerLocale as registerDatepickerLocale } from 'react-datepicker';
import Modal from 'react-modal';

import { ConnectedRouter } from 'connected-react-router';
import GA4React from 'ga-4-react';
import { PersistGate } from 'redux-persist/integration/react';
import * as Sentry from '@sentry/react';
import { default as datepickerJa } from 'date-fns/locale/ja';
import { SWRConfig } from 'swr';
import moment from 'moment';
import 'moment/locale/ja';

import fetcher from '@swrAPI/fetcher';
import onSwrError from '@swrAPI/onError';
import LabeledMultiSelectMenuPortalProvider from '@components/UI/LabeledInputs/LabeledMultiSelect/LabeledMultiSelectMenuPortalProvider';

import store, { persistor } from './store';
import { history } from './store/reducers';
import TranslatedApp from './containers/TranslatedApp';
import ErrorBoundary from './containers/ErrorBoundary';
import Zendesk from './containers/Zendesk';

if (process.env.NODE_ENV === 'production') {
  Sentry.init({
    dsn: process.env.REACT_APP_SENTRY_PUBLIC_DSN,
    environment: process.env.ENVIRONMENT,
    release: 'zookeep@' + process.env.RELEASE,
  });
}

Modal.setAppElement('#root');
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;

moment.updateLocale('ja', {
  months: '01月_02月_03月_04月_05月_06月_07月_08月_09月_10月_11月_12月'.split('_'),
  longDateFormat: {
    LL: 'YYYY年MM月Do',
    LLL: 'YYYY年MM月Do HH:mm',
  },
});

moment.updateLocale('en', {
  longDateFormat: {
    LL: 'DD MMM YYYY',
    LLL: 'DD MMM YYYY HH:mm',
  },
});

registerDatepickerLocale('ja', datepickerJa);

const swrOptions = {
  errorRetryCount: 3,
  revalidateOnMount: true,
  fetcher,
  onError: onSwrError,
};

const renderDOM = () => {
  ReactDOM.render(
    <Provider store={store}>
      <ErrorBoundary>
        <PersistGate loading={null} persistor={persistor}>
          <ConnectedRouter history={history}>
            <SWRConfig value={swrOptions}>
              <LabeledMultiSelectMenuPortalProvider>
                <TranslatedApp history={history} />
              </LabeledMultiSelectMenuPortalProvider>
              <Zendesk />
            </SWRConfig>
          </ConnectedRouter>
        </PersistGate>
      </ErrorBoundary>
    </Provider>,
    document.getElementById('root')
  );
};

if (process.env.ENVIRONMENT === 'production') {
  const ga4react = new GA4React(process.env.REACT_APP_GA_MEASUREMENT_ID);
  (async () => {
    try {
      await ga4react.initialize();
    } catch (error) {
      console.log(error);
    }
    renderDOM();
  })();
} else {
  renderDOM();
}
