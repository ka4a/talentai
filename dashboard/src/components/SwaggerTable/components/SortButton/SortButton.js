import React, { memo } from 'react';
import { AiFillCaretDown, AiFillCaretUp } from 'react-icons/ai';

import classnames from 'classnames';
import PropTypes from 'prop-types';

import { Typography } from '@components';

import styles from './SortButton.module.scss';

const SortButton = (props) => {
  const { state, setState, dataField, defaultSort, children } = props;
  const { ordering } = state.params;

  const orderingCol = ordering.startsWith('-') ? ordering.substr(1) : ordering;
  const currentField = orderingCol === dataField;
  const orderingAsc = !currentField || !ordering.startsWith('-');

  const onSort = () => {
    const defaultSortCol = defaultSort.startsWith('-')
      ? defaultSort.substr(1)
      : defaultSort;

    /* -> asc -> desc -> default */
    let newOrdering;
    if (defaultSortCol !== orderingCol && currentField && !orderingAsc) {
      newOrdering = defaultSort;
    } else if (currentField && orderingAsc) {
      newOrdering = `-${dataField}`;
    } else {
      newOrdering = dataField;
    }

    setState({
      params: {
        ...state.params,
        ordering: newOrdering,
      },
    });
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
  state: PropTypes.shape({}).isRequired,
  setState: PropTypes.func.isRequired,
  defaultSort: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

export default memo(SortButton);
