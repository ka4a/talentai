import { en, ja } from 'make-plural/plurals';
import { i18n } from '@lingui/core';

import catalogEn from './locales/en/messages';
import catalogJa from './locales/ja/messages';

i18n.loadLocaleData('en', { plurals: en });
i18n.loadLocaleData('ja', { plurals: ja });
i18n.load({
  en: catalogEn.messages,
  ja: catalogJa.messages,
});
i18n.activate('en');

export default i18n;
