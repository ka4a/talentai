import { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import { batch, useDispatch, useSelector } from 'react-redux';
import { useMount, useUnmount } from 'react-use';
import { useLocation } from 'react-router-dom';

import curry from 'lodash/curry';
import isEqual from 'lodash/isEqual';

import { isUserBelongToGroups } from '@utils';
import { resetTableParams, updateTableParam } from '@actions';
import { translateChoices } from '@utils/locale';

export const useDeepCompareMemoize = (value) => {
  const ref = useRef();

  if (!isEqual(value, ref.current)) {
    ref.current = value;
  }

  return ref.current;
};

// Used to translate choice labels after translation framework is initialized
export const useTranslatedChoices = (i18n, choices, labelField = 'name') => {
  return useMemo(() => translateChoices(i18n, choices, labelField), [
    choices,
    i18n,
    labelField,
  ]);
};

export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// used only in DealPipelineMetrics, remove when replace with one from 'react-use'
export const useToggle = (defaultState = false) => {
  const [value, setValue] = useState(defaultState);
  const [params, setParams] = useState();

  return {
    set: setValue,
    value,
    toggle(e, params = null) {
      setValue((value) => !value);
      if (params) setParams(params);
    },
    params,
  };
};

export const useIsAuthenticatedByRoles = (groups) => {
  const user = useSelector((state) => state.user);
  return isUserBelongToGroups(user, groups);
};

// This hook mostly fixes Safari issue with scroll, it works fine in Chrome
export const useScrollToTop = () => {
  const { pathname } = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
};

export const useTable = ({
  useGetData,
  defaultSort = null,
  paginationKey = null,
  params,
  storeKey,
  isPublic = false,
}) => {
  const { limit, search, offset, ordering } =
    useSelector((state) => state.table[storeKey]) ?? {};

  const defaultLimit = useSelector((state) =>
    isPublic
      ? state.settings.publicTablePageSize[paginationKey]
      : state.user.frontendSettings[paginationKey]
  );

  const dispatch = useDispatch();

  useMount(() => {
    const update = curry(updateTableParam)(storeKey);
    batch(() => {
      dispatch(resetTableParams(storeKey)); // table initialization
      dispatch(update('limit', defaultLimit ?? 25));
      dispatch(update('ordering', defaultSort));
      dispatch(update('paginationKey', paginationKey));
      if (defaultSort) dispatch(update('defaultSort', defaultSort));
    });
  });

  useUnmount(() => {
    dispatch(resetTableParams(storeKey));
  });

  return useGetData({ search, limit, offset, ordering, ...params });
};

export function useAsyncCallbackWithStatus(callback) {
  const [isInProgress, setIsInProgress] = useState(false);

  const awaitCallback = useCallback(
    async (...args) => {
      setIsInProgress(true);

      try {
        await callback(...args);
      } finally {
        setIsInProgress(false);
      }
    },
    [callback]
  );

  return [isInProgress, awaitCallback];
}
