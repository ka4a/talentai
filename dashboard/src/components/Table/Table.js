import React, { memo, useCallback, useMemo } from 'react';
import { Table as TableRS } from 'reactstrap';
import { batch, useDispatch } from 'react-redux';

import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { NoData } from '@components';
import { updateTableParam } from '@actions';

import Loading from '../UI/Loading';
import Typography from '../UI/Typography';
import TablePagination from './components/TablePagination';
import TableRow from './components/TableRow';
import TableRowHeader from './components/TableRowHeader';
import TableContext from './tableContext';

import styles from './Table.module.scss';

/**
 * Works with 'table' reducer
 * Used in combination with 'useTable' hook
 * It's REQUIRED to pass the same 'storeKey' to Table, TableHeader and useTable
 * If table doesn't use sorting AND pagination it can be used without useTable and storeKey
 */
const Table = (props) => {
  const {
    data,
    columns,
    onRowClick,
    isBigRow,
    isPublic,
    className,
    rowClasses,
    hidePagination,
    noDataMessage,
    noDataPlaceholder,
    hideHeader,
    isOpenColumn,
    withBorder,
    storeKey,
    activeRowId,
  } = props;

  const { loading, error } = data;
  const { results = [], count } = data.data ?? {};

  const dispatch = useDispatch();
  const onChangedPagination = useCallback(
    (offset, limit) => {
      batch(() => {
        dispatch(updateTableParam(storeKey, 'limit', limit));
        dispatch(updateTableParam(storeKey, 'offset', offset));
      });
    },
    [dispatch, storeKey]
  );

  const statusRow = useMemo(() => {
    if (loading) return <Loading />;

    if (error) {
      return (
        <Typography>
          <Trans>An error occurred.</Trans>
        </Typography>
      );
    }

    if (results.length === 0) return 'no_data';
  }, [error, loading, results.length]);

  const shouldShowHeader = results.length > 0 && !hideHeader;
  const shouldRenderResults = results.length > 0 && !loading && !error;

  let tableContent, placeholder;
  if (shouldRenderResults) {
    tableContent = (
      <tbody>
        {results.map((row, i) => (
          <TableRow
            row={row}
            key={row.id || i}
            columns={columns}
            onClick={onRowClick}
            rowClasses={rowClasses}
            isActive={row.id === activeRowId}
          />
        ))}
      </tbody>
    );
  } else if (statusRow === 'no_data') {
    // 'No Data' is not set as default value of noDataMessage,
    // because it won't be translated then
    const message = noDataMessage ?? t`No Data`;
    placeholder = noDataPlaceholder || <NoData message={message} />;
  } else {
    tableContent = (
      <tbody>
        <tr>
          <td colSpan={columns.length} className={styles.statusRow}>
            {statusRow}
          </td>
        </tr>
      </tbody>
    );
  }

  return (
    <TableContext.Provider value={{ isOpenColumn, storeKey, withBorder }}>
      <div
        className={classnames([
          'table-custom-wrapper',
          isBigRow ? styles.bigRow : styles.defaultRow,
        ])}
      >
        <TableRS className={classnames(styles.table, className)}>
          {shouldShowHeader && (
            <thead>
              <tr>
                {columns.map((col, i) => (
                  <TableRowHeader key={i} col={col} />
                ))}
              </tr>
            </thead>
          )}
          {tableContent}
        </TableRS>
        {placeholder}
      </div>

      {shouldRenderResults && !hidePagination && (
        <TablePagination
          isPublic={isPublic}
          count={count}
          onChange={onChangedPagination}
          marginPagesDisplayed={1}
          pageRangeDisplayed={3}
        />
      )}
    </TableContext.Provider>
  );
};

Table.propTypes = {
  data: PropTypes.shape({
    data: PropTypes.shape({
      results: PropTypes.array,
      count: PropTypes.number,
      loading: PropTypes.bool,
      error: PropTypes.any,
    }),
  }).isRequired,
  columns: PropTypes.arrayOf(
    PropTypes.shape({
      dataField: PropTypes.string,
      formatter: PropTypes.func,
      classes: PropTypes.string,
      hideInSidebar: PropTypes.bool,
      align: PropTypes.oneOf(['left', 'center', 'right']),
      sort: PropTypes.bool,
      width: PropTypes.number,
      text: PropTypes.string,
    })
  ).isRequired,
  activeRowId: PropTypes.number,
  hidePagination: PropTypes.bool,
  onRowClick: PropTypes.func,
  className: PropTypes.string,
  rowClasses: PropTypes.func,
  hideHeader: PropTypes.bool,
  isOpenColumn: PropTypes.bool,
  isBigRow: PropTypes.bool,
  noDataMessage: PropTypes.string,
  noDataPlaceholder: PropTypes.node,
  storeKey: PropTypes.string,
  withBorder: PropTypes.bool,
  isPublic: PropTypes.bool,
};

Table.defaultProps = {
  noDataMessage: null,
  hidePagination: false,
  onRowClick() {},
  isOpenColumn: false,
  hideHeader: false,
  withBorder: true,
  isBigRow: false,
  className: '',
  storeKey: '',
  rowClasses() {
    return '';
  },
};

export default memo(Table);
