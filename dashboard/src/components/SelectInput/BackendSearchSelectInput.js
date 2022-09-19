import React, { useState, useCallback, useMemo } from 'react';
import { Dropdown, DropdownMenu, DropdownToggle } from 'reactstrap';

import PropTypes from 'prop-types';
import _ from 'lodash';
import classnames from 'classnames';

import {
  useDebounce,
  useFocusIfTrue,
  useSwagger,
  useToggleStateForPortals,
} from '../../hooks';
import Portal from '../Portal';
import SelectSearchInput from './SelectSearchInput';
import Item from './Item';
import LocalPropTypes from './propTypes';
import DefaultTrigger from './DefaultTrigger';
import Loading from '../UI/Loading';

import styles from './SelectInput.module.scss';

BackendSearchSelectInput.propTypes = {
  operationId: PropTypes.string.isRequired,
  toOption: PropTypes.isRequired,
  TriggerComponent: LocalPropTypes.component,
  value: PropTypes.any,
  initialLabel: PropTypes.string,
  params: PropTypes.objectOf(PropTypes.any),
  delay: PropTypes.number,
  nullOption: PropTypes.string,
  disabled: PropTypes.bool,
  onSelect: PropTypes.func.isRequired,
  inline: PropTypes.bool,
  placeholder: PropTypes.string,
  direction: PropTypes.string,
  className: PropTypes.string,
  name: PropTypes.string,
};

BackendSearchSelectInput.defaultProps = {
  initialLabel: '',
  className: '',
  delay: 500,
  params: {},
  TriggerComponent: DefaultTrigger,
  triggerProps: PropTypes.object,
  direction: 'down',
};

function BackendSearchSelectInput(props) {
  const {
    disabled,
    onSelect,
    TriggerComponent,
    triggerProps,
    operationId,
    toOption,
    delay,
    nullOption,
    value,
    inline,
    placeholder,
    className,
    direction,
    name,
  } = props;

  const [search, setSearch] = useState('');
  const initialLabel = value == null && nullOption ? nullOption : props.initialLabel;
  const [label, setLabel] = useState(null);

  const delayedSearch = useDebounce(search, delay);
  const isSearchWaiting = search !== delayedSearch;

  const params = props.params ? { ...props.params } : {};

  if (delayedSearch !== '') params.search = delayedSearch;

  const swagger = useSwagger(operationId, params);

  const options = useMemo(() => {
    const realOptions = _.map(_.get(swagger, 'obj.results', []), toOption);
    return nullOption
      ? [{ label: nullOption, value: null }, ...realOptions]
      : realOptions;
  }, [toOption, nullOption, swagger]);

  const isOpen = useToggleStateForPortals();
  const searchRef = useFocusIfTrue(isOpen.value);
  const setIsOpen = isOpen.set;

  const handleSelect = useCallback(
    (option) => {
      setSearch('');
      setLabel(option.label);
      onSelect(option.value);
      setIsOpen(false);
    },
    [onSelect, setIsOpen]
  );

  const handleSearchKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && options.length) {
        handleSelect(options[0]);
      }
    },
    [options, handleSelect]
  );

  return (
    <Dropdown
      className={classnames(styles.selector, { 'd-inline-block': inline }, className)}
      isOpen={isOpen.value}
      toggle={isOpen.toggle}
      direction={direction}
    >
      <DropdownToggle className={styles.trigger} disabled={disabled}>
        <TriggerComponent
          placeholder={placeholder}
          value={label || initialLabel}
          disabled={disabled}
          name={name}
          {...triggerProps}
        />
      </DropdownToggle>
      <Portal>
        <DropdownMenu className={styles.menu}>
          <div ref={isOpen.containerRef}>
            <div className='mb-2 px-2'>
              <SelectSearchInput
                innerRef={searchRef}
                value={search}
                setValue={setSearch}
                onKeyDown={handleSearchKeyDown}
                disabled={!options.length}
              />
            </div>
            {isSearchWaiting || swagger.loading ? (
              <div className='pt-2'>
                <Loading />
              </div>
            ) : (
              _.map(options, (option) => {
                return (
                  <Item
                    key={option.value}
                    value={option.value}
                    selected={value === option.value}
                    onSelect={() => {
                      handleSelect(option);
                    }}
                  >
                    {option.label}
                  </Item>
                );
              })
            )}
          </div>
        </DropdownMenu>
      </Portal>
    </Dropdown>
  );
}

export default BackendSearchSelectInput;
