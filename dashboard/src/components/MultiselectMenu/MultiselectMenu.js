import React, { memo, Fragment, useMemo, useState } from 'react';
import { Button, Dropdown, DropdownMenu, DropdownToggle } from 'reactstrap';

import _ from 'lodash';
import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import {
  useFocusIfTrue,
  useMarkedOptions,
  useToggleStateForPortals,
} from '../../hooks';
import LocalPropTypes from './propTypes';
import Portal from '../Portal';
import ItemWithCheckbox from './ItemWithCheckbox';
import SelectSearchInput from '../SelectInput/SelectSearchInput';

import styles from './MultiselectMenu.module.scss';

const getValue = (option) => option.value;

const clearInsignOptions = (options) =>
  _.filter(options, (option) => option.type !== 'title');

function MultiselectMenu(props) {
  const {
    children,
    selected,
    onSelectionChange,
    options,
    direction,
    searchable,
  } = props;

  const isOpen = useToggleStateForPortals();
  const searchRef = useFocusIfTrue(isOpen.value);

  const selectedArray = useMemo(() => _.castArray(selected), [selected]);

  const markedOptions = useMarkedOptions(options, selectedArray);

  const [search, setSearch] = useState(null);

  function selectOne(value, shouldAdd) {
    onSelectionChange(
      shouldAdd ? [...selectedArray, value] : _.without(selectedArray, value)
    );
  }

  function selectAll() {
    onSelectionChange(_.map(clearInsignOptions(options), getValue));
  }

  function clearSelection() {
    onSelectionChange([]);
  }

  function getDisplayOptions() {
    if (searchable && search) {
      return _.filter(markedOptions, (option) =>
        _.includes(option.label.toLowerCase(), search.toLowerCase())
      );
    }
    return markedOptions;
  }

  return (
    <Dropdown
      className={styles.selector}
      isOpen={isOpen.value}
      toggle={isOpen.toggle}
      direction={direction}
    >
      <DropdownToggle className={styles.trigger}>{children}</DropdownToggle>
      <Portal>
        <DropdownMenu
          right
          className={styles.menu}
          modifiers={{
            setMaxHeight: {
              enabled: true,
              fn: (data) => ({
                ...data,
                styles: {
                  ...data.styles,
                  overflow: 'auto',
                  maxHeight: 400,
                },
              }),
            },
          }}
        >
          <div ref={isOpen.containerRef}>
            {searchable ? (
              <div className='px-3 pt-1 pb-3'>
                <SelectSearchInput
                  innerRef={searchRef}
                  setValue={setSearch}
                  disabled={!options.length}
                />
              </div>
            ) : null}
            {_.map(getDisplayOptions(), (option) => (
              <Fragment key={option.value || option.label}>
                {option.type === 'title' && (
                  <div
                    className='
                    d-flex justify-content-end
                    px-3 text-primary font-weight-bold fs-18'
                  >
                    {option.label}
                  </div>
                )}
                {!option.type && (
                  <ItemWithCheckbox
                    {...option}
                    key={option.value}
                    onSelect={selectOne}
                  />
                )}
              </Fragment>
            ))}
            <div className={styles.funcPanel}>
              <Button onClick={selectAll} className='btn-inv-primary'>
                <Trans>Select All</Trans>
              </Button>
              {' / '}
              <Button onClick={clearSelection} className='btn-inv-primary'>
                <Trans>Clear</Trans>
              </Button>
            </div>
          </div>
        </DropdownMenu>
      </Portal>
    </Dropdown>
  );
}

MultiselectMenu.propTypes = {
  selected: PropTypes.oneOfType([
    LocalPropTypes.value,
    PropTypes.arrayOf(LocalPropTypes.value),
  ]),
  onSelectionChange: PropTypes.func,
  direction: PropTypes.oneOf(['up', 'down', 'left', 'right']),
  options: LocalPropTypes.options,
  optionTypes: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string,
      label: PropTypes.object, // translated string
    })
  ),
  searchable: PropTypes.bool,
};

MultiselectMenu.defaultProps = {
  onSelectionChange() {},
  selected: [],
  direction: 'down',
  options: [],
  searchable: false,
};

export default memo(MultiselectMenu);
