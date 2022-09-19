import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { I18nProvider } from '@lingui/react';
import { detect, fromNavigator } from '@lingui/detect-locale';
import Cookies from 'js-cookie';
import moment from 'moment';

import { changeLocale } from '@actions';

import i18n from '../i18n';
import App from './App';

const AVAILABLE_LOCALES = ['en', 'ja'];
const FALLBACK_LOCALE = 'en';

const TranslatedApp = () => {
  const locale = useSelector((state) => state.settings.locale);
  const dispatch = useDispatch();

  useEffect(() => {
    if (locale) return;

    let detectedLocale = detect(fromNavigator(), FALLBACK_LOCALE);
    if (!AVAILABLE_LOCALES.includes(detectedLocale)) detectedLocale = FALLBACK_LOCALE;

    dispatch(changeLocale(detectedLocale));
  }, [dispatch, locale]);

  useEffect(() => {
    i18n.activate(locale);
    moment.locale(locale);
    Cookies.set('django_language', locale);
    Cookies.set('lang', locale);
  }, [dispatch, locale]);

  if (!locale) return null;

  return (
    <I18nProvider i18n={i18n}>
      <App />
    </I18nProvider>
  );
};

export default TranslatedApp;
