import React, { memo, useCallback, useMemo, useState } from 'react';
import CreatableSelect from 'react-select/creatable';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';
import differenceBy from 'lodash/differenceBy';

import { Typography } from '@components';
import { useTagsList } from '@swrAPI';

import styles from './TagsInput.module.scss';

const TagsInput = ({ tags, onSave, tagType }) => {
  const [inputValue, setInputValue] = useState('');

  const { data } = useTagsList(tagType);

  const selectedOptions = useMemo(
    () => tags?.map(({ name }) => ({ value: name, name })) ?? [],
    [tags]
  );

  const availableOptions = useMemo(() => {
    // do not show selected options in menu list
    const allOptions = data.map(({ id, name }) => ({ value: id, name }));
    return differenceBy(allOptions, selectedOptions, 'name');
  }, [data, selectedOptions]);

  // handlers
  const onChange = useCallback((options) => onSave(options), [onSave]);

  const onKeyDown = useCallback(
    (event) => {
      const isAlreadyAdded = Boolean(tags?.find((el) => el.name === inputValue));
      const isEmpty = !inputValue.trim();
      const isDesiredKey = event.key === 'Enter' || event.key === ',';

      // forbid to input ','
      if (event.key === ',') event.preventDefault();

      if (isDesiredKey && !isAlreadyAdded && !isEmpty) {
        event.preventDefault();

        onSave([...(tags ?? []), { name: inputValue }]);
        setInputValue('');
      }
    },
    [inputValue, onSave, tags]
  );

  const onInputChange = useCallback((inputValue) => {
    setInputValue(inputValue);
  }, []);

  const getOptionLabel = useCallback((option) => {
    /**
     * new options are created by default in format { value, label }
     * 'value' is an input value, that's what we need
     */
    if (option.__isNew__) return option.value;
    return option.name;
  }, []);

  return (
    <div className={styles.wrapper}>
      <label className={styles.label}>
        <Typography variant='caption'>
          <Trans>Skills</Trans>
        </Typography>
      </label>

      <CreatableSelect
        value={selectedOptions}
        inputValue={inputValue}
        options={availableOptions}
        onChange={onChange}
        onInputChange={onInputChange}
        onKeyDown={onKeyDown}
        getOptionLabel={getOptionLabel}
        classNamePrefix='multiselect'
        className={styles.multiselect}
        closeMenuOnSelect={false}
        isMulti
      />
    </div>
  );
};

TagsInput.propTypes = {
  tags: PropTypes.arrayOf(PropTypes.shape({})).isRequired,
  tagType: PropTypes.oneOf(['candidate', 'skill']).isRequired,
  onSave: PropTypes.func.isRequired,
};

export default memo(TagsInput);
