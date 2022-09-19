import React from 'react';

import PropTypes from 'prop-types';

import Checkbox from '../UI/Checkbox';
import LocalPropTypes from './propTypes';

import styles from './MultiselectMenu.module.scss';

function ItemWithCheckbox({ onSelect, value, isSelected, label }) {
  const select = () => {
    onSelect(value, !isSelected);
  };

  return (
    <div className={styles.item}>
      <Checkbox checked={isSelected} onChange={select} />
      <button className={styles.itemLabel} onClick={select}>
        {label}
      </button>
    </div>
  );
}

ItemWithCheckbox.propTypes = {
  onSelect: PropTypes.func,
  value: LocalPropTypes.value.isRequired,
  isSelected: PropTypes.bool,
  label: PropTypes.string,
};
ItemWithCheckbox.defaultProps = {
  onSelect() {},
  isSelected: false,
  label: '',
};

export default ItemWithCheckbox;
