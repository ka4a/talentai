import React, { memo, useMemo, useState } from 'react';
import { Dropdown, DropdownMenu, DropdownToggle } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import _ from 'lodash';

import { useFocusIfTrue, useToggleStateForPortals } from '../../hooks';
import LocalPropTypes from './propTypes';
import DefaultTrigger from './DefaultTrigger';
import Portal from '../Portal';
import Item from './Item';
import SelectSearchInput from './SelectSearchInput';

import styles from './SelectInput.module.scss';

function addSearchValueOnTop(options, newOption, getLabel) {
  const result = [];
  options.forEach((option) => {
    if (getLabel(option) === getLabel(newOption)) newOption = option;
    else result.push(option);
  });
  result.unshift(newOption);
  return result;
}

function Selector(props) {
  const {
    className,
    name,
    value,
    TriggerComponent,
    triggerComponentProps,
    onSelect,
    options,
    direction,
    disabled,
    getValue,
    getLabel,
    placeholder,
    inline,
    searchable,
    notStrictSearch,
    toOption,
  } = props;

  const select = (s) => {
    setSearch('');
    onSelect(s);
    isOpen.set(false);
  };

  const [search, setSearch] = useState('');

  const isOpen = useToggleStateForPortals();
  const searchRef = useFocusIfTrue(isOpen.value);

  const option = useMemo(() => {
    const option = _.find(options, (entry) => getValue(entry) === value);
    if (!option && notStrictSearch) {
      return toOption(value);
    }

    return option;
  }, [getValue, options, value, notStrictSearch, toOption]);

  const label = useMemo(() => getLabel(option), [option, getLabel]);

  const filteredOptions = useMemo(() => {
    if (!(searchable && search)) return options;

    const filtered = _.filter(options, (option) =>
      _.includes(getLabel(option).toLowerCase(), search.toLowerCase())
    );

    return notStrictSearch
      ? addSearchValueOnTop(filtered, toOption(search), getLabel)
      : filtered;
  }, [options, searchable, search, notStrictSearch, getLabel, toOption]);

  return (
    <Dropdown
      className={classnames(styles.selector, { 'd-inline-block': inline }, className)}
      isOpen={isOpen.value}
      toggle={isOpen.toggle}
      direction={direction}
    >
      <DropdownToggle className={styles.trigger} disabled={disabled}>
        <TriggerComponent
          {...triggerComponentProps}
          placeholder={placeholder || value}
          value={label}
          name={name}
          disabled={disabled}
        />
      </DropdownToggle>

      <Portal>
        <DropdownMenu className={styles.menu}>
          <div ref={isOpen.containerRef}>
            {searchable && (
              <div className='mb-2 px-2'>
                <SelectSearchInput
                  innerRef={searchRef}
                  value={search}
                  setValue={setSearch}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && filteredOptions.length) {
                      select(filteredOptions[0].value);
                    }
                  }}
                  disabled={!notStrictSearch && !options.length}
                  mode='form'
                />
              </div>
            )}
            {_.map(filteredOptions, (option) => {
              const optionValue = getValue(option);
              return (
                <Item
                  key={optionValue}
                  value={optionValue}
                  selected={value === optionValue}
                  onSelect={() => {
                    select(optionValue);
                  }}
                >
                  {getLabel(option)}
                </Item>
              );
            })}
          </div>
        </DropdownMenu>
      </Portal>
    </Dropdown>
  );
}

Selector.propTypes = {
  id: PropTypes.string,
  className: PropTypes.string,
  TriggerComponent: PropTypes.oneOfType([
    PropTypes.func,
    PropTypes.instanceOf(React.Component),
  ]),
  triggerComponentProps: PropTypes.object,
  value: LocalPropTypes.value,
  name: PropTypes.string,
  placeholder: PropTypes.string,
  onSelect: PropTypes.func,
  getLabel: PropTypes.func,
  getValue: PropTypes.func,
  direction: PropTypes.oneOf(['up', 'down', 'left', 'right']),
  options: LocalPropTypes.options,
  inline: PropTypes.bool,
  searchable: PropTypes.bool,
  notStrictSearch: PropTypes.bool,
  toOption: PropTypes.func,
};

Selector.defaultProps = {
  id: null,
  triggerComponentProps: {},
  TriggerComponent: DefaultTrigger,
  value: null,
  name: null,
  onSelect() {},
  placeholder: null,
  getLabel(option, placeholder, value) {
    if (option) return option.name || option.label;
    if (placeholder !== null) return placeholder;
    console.error(
      `SelectInput: option for value ${value} is missing and placeholder isn't specified`
    );
    return value;
  },
  getValue(option) {
    return option ? option.value : null;
  },
  toOption: (value) => ({ label: value, value }),
  direction: 'down',
  options: [],
  inline: false,
};

export default memo(Selector);
