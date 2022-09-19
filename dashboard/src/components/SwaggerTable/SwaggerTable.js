import React, { memo, useCallback, useEffect, useMemo } from 'react';
import { useSelector } from 'react-redux';
import { Table } from 'reactstrap';

import { Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { useDeepCompareMemoize } from '@hooks';
import { NoData } from '@components';

import Loading from '../UI/Loading';
import Typography from '../UI/Typography';
import TablePagination from './components/TablePagination';
import TableRow from './components/TableRow';
import TableRowHeader from './components/TableRowHeader';

import styles from './SwaggerTable.module.scss';

// LEGACY component, use Table instead
const SwaggerTable = (props) => {
  const {
    columns,
    getRowKey,
    className,
    rowClasses,
    defaultSort,
    fetchFn,
    hideHeader,
    paginationKey,
    primaryLink,
    params,
    state,
    setState,
    primaryLinkNewTab,
    hidePagination,
    onRowClick,
    isOpenColumn,
    isBigRow,
    hideIfEmpty,
    noDataMessage,
  } = props;

  const {
    data: { results, count },
    loading,
    error,
  } = state;

  const frontendSettings = useSelector((state) => state.user.frontendSettings);

  const combinedParams = useDeepCompareMemoize({
    ...state.params,
    ...params,
    limit: frontendSettings?.[paginationKey] ?? 25,
  });

  useEffect(() => {
    if (!state.initialized) {
      setState({
        initialized: true,
        params: {
          ...state.params,
          ordering: state.params.ordering || defaultSort,
        },
      });
    }
  }, [defaultSort, setState, state.initialized, state.params]);

  useEffect(() => {
    if (!state.initialized) return;

    let didCancel = false;

    fetchFn(combinedParams).then((newState) => {
      if (!didCancel) setState(newState);
    });

    return () => {
      didCancel = true;
    };
  }, [combinedParams, fetchFn, setState, state.initialized]);

  const onChangedPagination = useCallback(
    (offset, limit) => {
      setState((state) => ({
        params: { ...state.params, offset, limit },
      }));
    },
    [setState]
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

    if (results.length === 0) return 'NoData';
  }, [error, loading, results.length]);

  const shouldRenderResults = results.length > 0 && !loading && !error;
  const shouldRenderStatus = (results.length === 0 || loading || error) && !hideIfEmpty;
  const shouldShowHeader = !hideHeader && results.length > 0 && !hideIfEmpty;

  if (!state.initialized) return null;

  return (
    <div>
      <div
        className={classnames([
          'table-custom-wrapper',
          styles.tableWrapper,
          isBigRow ? styles.bigRow : styles.defaultRow,
        ])}
      >
        <Table className={classnames(styles.table, className)}>
          {shouldShowHeader && (
            <thead>
              <tr>
                {columns.map((col, i) => (
                  <TableRowHeader
                    key={i}
                    col={col}
                    defaultSort={defaultSort}
                    state={state}
                    setState={setState}
                    isOpenColumn={isOpenColumn}
                  />
                ))}
              </tr>
            </thead>
          )}

          {shouldRenderResults && (
            <tbody>
              {results.map((row) => (
                <TableRow
                  row={row}
                  columns={columns}
                  key={getRowKey(row)}
                  onClick={onRowClick}
                  getLink={primaryLink}
                  rowClasses={rowClasses}
                  isOpenColumn={isOpenColumn}
                  shouldOpenTab={primaryLinkNewTab}
                />
              ))}
            </tbody>
          )}

          {shouldRenderStatus &&
            (statusRow === 'NoData' ? (
              <NoData message={noDataMessage} />
            ) : (
              <tbody>
                <tr>
                  <td colSpan={columns.length} className={styles.statusRow}>
                    {statusRow}
                  </td>
                </tr>
              </tbody>
            ))}
        </Table>
      </div>

      {shouldRenderResults && !hidePagination && (
        <TablePagination
          count={count}
          offset={state.params.offset}
          limit={state.params.limit}
          pageRangeDisplayed={3}
          marginPagesDisplayed={1}
          onChange={onChangedPagination}
          paginationKey={paginationKey}
          isOpenColumn={isOpenColumn}
        />
      )}
    </div>
  );
};

SwaggerTable.propTypes = {
  columns: PropTypes.arrayOf(
    PropTypes.shape({
      dataField: PropTypes.string,
      formatter: PropTypes.func,
      headerFormatter: PropTypes.func,
      classes: PropTypes.string,
      hideInSidebar: PropTypes.bool,
      align: PropTypes.oneOf(['left', 'center', 'right']),
      sort: PropTypes.bool,
      filter: PropTypes.func,
      preventRowMouseEvents: PropTypes.bool,
      width: PropTypes.number,
    })
  ).isRequired,
  className: PropTypes.string,
  primaryLink: PropTypes.func,
  primaryLinkNewTab: PropTypes.bool,
  defaultSort: PropTypes.string,
  getRowKey: PropTypes.func,
  rowClasses: PropTypes.func,
  onRowClick: PropTypes.func,
  hideHeader: PropTypes.bool,
  paginationKey: PropTypes.string,

  params: PropTypes.object,
  fetchFn: PropTypes.func.isRequired,
  state: PropTypes.object.isRequired,
  setState: PropTypes.func.isRequired,
  hideTopPagination: PropTypes.bool,

  isOpenColumn: PropTypes.bool,
  hideIfEmpty: PropTypes.bool,
  isBigRow: PropTypes.bool,
  noDataMessage: PropTypes.string,
};

SwaggerTable.defaultProps = {
  getRowKey: (row, i) => row.id || i,
  hideHeader: false,
  hidePagination: false,
  hideIfEmpty: false,
  isBigRow: false,
  noDataMessage: 'No Data',
  defaultSort: '',
  isOpenColumn: false,
};

export default memo(SwaggerTable);
