import React, { memo, useContext } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AiFillCaretDown, AiFillCaretUp } from 'react-icons/ai';

import classnames from 'classnames';
import PropTypes from 'prop-types';

import { Typography } from '@components';
import { updateTableParam } from '@actions';

import TableContext from '../../tableContext';

import styles from './SortButton.module.scss';

const pruneDash = (value) => (value?.startsWith('-') ? value.substr(1) : value);

const SortButton = ({ dataField, children }) => {
  const { storeKey } = useContext(TableContext);

  const ordering = useSelector((state) => state.table[storeKey]?.ordering);
  const defaultSort = useSelector((state) => state.table[storeKey]?.defaultSort);

  const orderingCol = pruneDash(ordering);
  const currentField = orderingCol === dataField;
  const orderingAsc = !currentField || !ordering.startsWith('-');

  const dispatch = useDispatch();

  const onSort = () => {
    const defaultSortCol = pruneDash(defaultSort);

    /* -> asc -> desc -> default */
    let newOrdering;

    if (defaultSortCol !== orderingCol && currentField && !orderingAsc) {
      newOrdering = defaultSort;
    } else if (currentField && orderingAsc) {
      newOrdering = `-${dataField}`;
    } else {
      newOrdering = dataField;
    }

    dispatch(updateTableParam(storeKey, 'ordering', newOrdering));
  };

  const activeStyle = { [styles.active]: currentField };

  return (
    <div className={styles.button} onClick={onSort}>
      <Typography variant='caption' className={classnames(activeStyle)}>
        {children}
      </Typography>

      <span className={classnames([styles.icon, activeStyle])}>
        {orderingAsc ? <AiFillCaretUp /> : <AiFillCaretDown />}
      </span>
    </div>
  );
};

SortButton.propTypes = {
  dataField: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

export default memo(SortButton);
