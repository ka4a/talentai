import React, { useState } from 'react';
import { MdChevronRight, MdExpandMore } from 'react-icons/md';
import { Button } from 'reactstrap';

import _ from 'lodash';
import { useLingui } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { Loading } from '@components/UI/Loading';

import Checkbox from '../../../../components/UI/Checkbox';

import styles from './AgencyDirectory.module.scss';

const Filter = React.memo(function Filter(props) {
  const { group, categories, categoryFilter, onToggle } = props;
  const [opened, setOpened] = useState(true);
  const [more, setMore] = useState(false);

  const renderedCategories = more ? categories : _.slice(categories, 0, 6);

  return (
    <>
      <div className='d-flex'>
        <div className='font-weight-bold text-uppercase'>{group}</div>
        <div className='ml-auto'>
          <Button color='link' className='p-0' onClick={() => setOpened(!opened)}>
            {opened ? <MdExpandMore size='1.5em' /> : <MdChevronRight size='1.5em' />}
          </Button>
        </div>
      </div>
      {opened ? (
        <div className='mt-16'>
          {_.map(renderedCategories, (c) => (
            <div key={c.id}>
              <label className='w-100'>
                <Checkbox
                  onChange={(e) => {
                    e.preventDefault();
                    onToggle(c.id);
                  }}
                  checked={_.includes(categoryFilter, c.id)}
                />
                <span className='fs-14 ml-8'>{c.title}</span>
              </label>
            </div>
          ))}
          {more ? (
            <Button className='btn-inv-secondary' onClick={() => setMore(false)}>
              <Trans>See Less</Trans>
            </Button>
          ) : (
            <Button className='btn-inv-primary' onClick={() => setMore(true)}>
              <Trans>See More</Trans>
            </Button>
          )}
        </div>
      ) : null}
      <hr />
    </>
  );
});

export const AgencyDirectoryFilters = React.memo(function AgencyDirectoryFilters(
  props
) {
  const {
    loading,
    categoryGroups,
    categories,
    categoryFilter,
    onToggle,
    functionFocus,
    functionFocusFilter,
    onFunctionFocusToggle,
    onClear,
  } = props;

  const { i18n } = useLingui();

  const categoriesPerGroup = _.chain(categories).groupBy('group').value();

  return (
    <div className={styles.container}>
      <div className='d-flex'>
        <div className='fs-18 font-weight-bold mb-16'>
          <Trans>Filters</Trans>
        </div>
        <div className='ml-auto'>
          <Button className='btn-inv-primary p-0' onClick={onClear}>
            <Trans>Clear</Trans>
          </Button>
        </div>
      </div>
      {loading && <Loading />}
      {!loading ? (
        <>
          <Filter
            group={i18n._(t`Function Focus`)}
            categories={functionFocus}
            categoryFilter={functionFocusFilter}
            onToggle={onFunctionFocusToggle}
          />
          {_.map(categoryGroups, (g) => (
            <Filter
              key={g}
              group={g}
              categories={categoriesPerGroup[g]}
              categoryFilter={categoryFilter}
              onToggle={onToggle}
            />
          ))}
        </>
      ) : null}
    </div>
  );
});
