import React, { useCallback } from 'react';
import { IoIosGlobe } from 'react-icons/all';
import { useDispatch, useSelector } from 'react-redux';

import { LOCALE_CHOICES } from '@constants';
import { Dropdown } from '@components';
import IconButton from '@components/UI/IconButton';
import { changeLocale, updateUser } from '@actions';

const LOCALE_OPTIONS = LOCALE_CHOICES.map((choice) => ({
  id: choice.value,
  label: choice.name,
}));

function LanguageMenu() {
  const dispatch = useDispatch();
  const isAuthenticated = useSelector(({ user }) => user?.isAuthenticated);

  const locale = useSelector(({ settings }) => settings.locale);

  const handleChangeLocale = useCallback(
    (option) => {
      if (isAuthenticated) {
        dispatch(updateUser({ locale: option.id }));
      }
      dispatch(changeLocale(option.id));
    },
    [dispatch, isAuthenticated]
  );

  return (
    <Dropdown
      trigger={
        <IconButton>
          <IoIosGlobe size={22} />
        </IconButton>
      }
      selected={locale}
      options={LOCALE_OPTIONS}
      handleChange={handleChangeLocale}
    />
  );
}

export default LanguageMenu;
