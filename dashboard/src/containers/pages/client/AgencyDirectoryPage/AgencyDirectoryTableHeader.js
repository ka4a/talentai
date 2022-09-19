import React, { useCallback } from 'react';

import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { SearchInput, SelectInput } from '@components';

const SORT_OPTIONS = [
  { value: '-contract_ann,nam', name: t`Alphabetical` },
  { value: '-contract_ann,-name', name: t`Alphabetical (desc)` },
];

function TableHeader({ state, setState, i18n }) {
  const ordering = state.params.ordering;

  const onSortSelect = useCallback(
    (ordering) => {
      setState({
        params: {
          ...state.params,
          ordering,
        },
      });
    },
    [state, setState]
  );

  return (
    <div className='mb-16 d-flex flex-wrap'>
      <div className='pr-16' style={{ flexGrow: 3 }}>
        <SearchInput
          className='w-100'
          inputAttrs={{ bsSize: 'lg' }}
          placeholder={i18n._(t`Search Agencies`)}
          state={state}
          setState={setState}
          mode='form'
        />
      </div>
      <div style={{ flexGrow: 1 }}>
        <SelectInput
          placeholder={i18n._(t`Sort`)}
          value={ordering || ''}
          onSelect={onSortSelect}
          options={SORT_OPTIONS}
        />
      </div>
    </div>
  );
}

TableHeader.propTypes = {
  state: PropTypes.object.isRequired,
  setState: PropTypes.func.isRequired,
};

export default withI18n()(TableHeader);
