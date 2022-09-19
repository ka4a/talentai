import { toast } from 'react-toastify';
import { ZendeskAPI } from 'react-zendesk';

import moment from 'moment';
import { i18n } from '@lingui/core';
import colorConvert from 'color-convert';

export const delay = (timeout) => {
  return new Promise((resolve) => {
    setTimeout(resolve, timeout);
  });
};

export const httpsReg = /((^http(s)?:\/\/)|^)/;
export const replaceHttps = (url) => {
  const isValidUrl = url && typeof url === 'string';
  return isValidUrl ? url.replace(httpsReg, 'https://') : url;
};

export const clearNumberStr = (value) => {
  // replaces only spaces and commas, so something like 10o is not passed
  // for validation
  if (typeof value === 'number') return value;
  const cleanValue = value.replace(/[\s,]+/g, '');

  return cleanValue || null;
};

export const showErrorToast = (error, params) => {
  toast.error(error, {
    position: 'bottom-center',
    autoClose: true,
    className: 'toast-alert',
    closeOnClick: true,
    ...params,
  });
};

export const showSuccessToast = (message) => {
  toast.success(message, {
    position: 'bottom-center',
    closeOnClick: true,
    className: 'toast-alert',
  });
};

export const getRelease = () => process.env['RELEASE'] || 'unknown';

export const getCssColorForId = (id = 1) => {
  const color = colorConvert.hsv.rgb((id * 12345) % 360, 42, 92);
  return `#${colorConvert.rgb.hex(...color)}`;
};

export const getTimezoneOffset = () => {
  let offset = moment.tz.zone(moment.tz.guess()).utcOffset(moment());
  const sign = offset < 0 ? '+' : '-';

  offset = Math.abs(offset);
  const hours = Math.floor(offset / 60);
  const minutes = offset % 60;

  return minutes ? `${sign}${hours}:${minutes}` : `${sign}${hours}`;
};

export const getChoiceName = (choices, value, key = 'name') => {
  return choices.find((el) => el.value === value)?.[key];
};

export const mapChoiceNamesByValue = (
  choices,
  valueKey = 'value',
  nameKey = 'name'
) => {
  const choiceMap = {};
  for (let choice of choices) {
    choiceMap[choice[valueKey]] = choice[nameKey];
  }
  return choiceMap;
};

export const formatNumber = ({ value, currency }) => {
  if (!value) return '';

  let options = { notation: 'compact' };

  if (currency) {
    options.style = 'currency';
    options.currencyDisplay = 'symbol';
    options.currency = currency;
  }

  return i18n.number(value, options);
};

export const openZendeskForm = () => {
  ZendeskAPI('webWidget', 'show'); // show launcher
  ZendeskAPI('webWidget', 'open'); // open form
};

export const isDialogConfirmed = async (dialogPromise) => {
  try {
    await dialogPromise;
    return true;
  } catch {
    return false;
  }
};

export const isDialogCanceled = async (dialogPromise) => {
  try {
    await dialogPromise;
    return false;
  } catch {
    return true;
  }
};

const noop = () => {};

export const warningDialog = (dialogPromise) => dialogPromise.catch(noop);

export const makeSingletonPromiseCreator = (createPromise) => {
  let promise = null;
  const removePromise = () => {
    promise = null;
  };

  return (...args) => {
    if (!promise) promise = createPromise(...args).then(removePromise, removePromise);
    return promise;
  };
};
