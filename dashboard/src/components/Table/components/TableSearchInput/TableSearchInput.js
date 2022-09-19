import React, { memo, useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { MdSearch } from 'react-icons/md';
import { Input } from 'reactstrap';

import { t } from '@lingui/macro';

import { updateTableParam } from '@actions';
import { useDebounce } from '@hooks';

import styles from './TableSearchInput.module.scss';

const TableSearchInput = ({ storeKey }) => {
  const [search, setSearch] = useState('');

  const debouncedSearchValue = useDebounce(search, 200);

  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(updateTableParam(storeKey, 'search', debouncedSearchValue));
  }, [debouncedSearchValue, dispatch, storeKey]);

  return (
    <div className={styles.container}>
      <Input
        value={search}
        className={`${styles.input} search-field`}
        onChange={(event) => {
          setSearch(event.target.value);
        }}
        placeholder={t`Search...`}
      />

      <div className={styles.iconContainer}>
        <MdSearch size={18} />
      </div>
    </div>
  );
};

export default memo(TableSearchInput);
