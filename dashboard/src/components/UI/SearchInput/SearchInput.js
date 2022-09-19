import React, { memo, useEffect, useState } from 'react';
import { Input } from 'reactstrap';
import { MdSearch } from 'react-icons/md';

import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { useDebounce } from '@hooks';

import styles from './SearchInput.module.scss';

const SearchInput = (props) => {
  const { className, placeholder, inputAttrs, state, setState, mode } = props;

  /**
   * if mode is 'regular', than this component accepts directly 'search' and 'setSearch' props
   * otherwise if this is a 'form' than 'state' is set of options including 'search'
   */
  const isRegularSearch = mode === 'regular';

  const { i18n } = useLingui();

  const [value, setValue] = useState(isRegularSearch ? state : state.params.search);
  const debouncedSearchValue = useDebounce(value, 200);

  useEffect(() => {
    if (isRegularSearch) {
      setState(debouncedSearchValue);
    } else {
      setState((state) => ({
        params: { ...state.params, search: debouncedSearchValue, offset: 0 },
      }));
    }
  }, [debouncedSearchValue, isRegularSearch, setState]);

  return (
    <div className={classnames(styles.container, className)}>
      <Input
        className={`${styles.input} search-field`}
        value={value}
        onChange={(event) => {
          setValue(event.target.value);
        }}
        placeholder={placeholder || i18n._(t`Search...`)}
        {...inputAttrs}
      />

      <div className={styles.iconContainer}>
        <MdSearch size={18} />
      </div>
    </div>
  );
};

SearchInput.propTypes = {
  state: PropTypes.oneOfType([PropTypes.string, PropTypes.shape({})]).isRequired,
  setState: PropTypes.func.isRequired,
  mode: PropTypes.oneOf(['regular', 'form']).isRequired,
  className: PropTypes.string,
};

SearchInput.defaultProps = {
  className: '',
};

export default memo(SearchInput);
