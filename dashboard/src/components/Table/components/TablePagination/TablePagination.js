import React, { memo, useCallback, useContext, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { Trans } from '@lingui/macro';

import TableContext from '@components/Table/tableContext';
import { setPublicTablePageSize, updateUserTablePageSize } from '@actions';

import Dropdown from '../../../UI/Dropdown';
import Typography from '../../../UI/Typography';
import PagesTrigger from '../PagesTrigger';
import usePages from './usePages';

import styles from './TablePagination.module.scss';

const TablePagination = (props) => {
  const { count, pageRangeDisplayed, marginPagesDisplayed, onChange, isPublic } = props;

  const { isOpenColumn, storeKey } = useContext(TableContext);

  const paginationSchema = useSelector(
    (state) => state.settings.localeData.paginationSchema ?? []
  );
  const { limit, offset, paginationKey } =
    useSelector((state) => state.table[storeKey]) ?? {};

  const dispatch = useDispatch();

  const {
    pages,
    pageFirstItemNumber,
    pageLastItemNumber,
    currentPage,
    maxPage,
  } = usePages({
    offset,
    limit,
    count,
    marginPagesDisplayed,
    pageRangeDisplayed,
  });

  const updatePageSize = useCallback(
    ({ id }) => {
      const setTableSize = isPublic ? setPublicTablePageSize : updateUserTablePageSize;
      dispatch(setTableSize(paginationKey, id));

      onChange(0, id);
    },
    [dispatch, onChange, paginationKey, isPublic]
  );

  const isPreviousDisabled = currentPage <= 1;
  const isNextDisabled = currentPage >= maxPage;

  const dropdownOptions = useMemo(
    () =>
      paginationSchema.map((opt) => ({
        id: opt,
        label: String(opt),
      })),
    [paginationSchema]
  );

  return (
    <div
      className={classnames(styles.pagination, 'table-pagination', {
        [styles.centered]: isOpenColumn,
      })}
    >
      {paginationKey && !isOpenColumn && (
        <Typography variant='caption' className={styles.counter}>
          <Trans>
            {pageFirstItemNumber}-{pageLastItemNumber} out of {count} items
          </Trans>
        </Typography>
      )}

      {count > limit && (
        <div className={styles.buttonsWrapper}>
          <button
            className={classnames(styles.previousNext, {
              [styles.disabled]: isPreviousDisabled,
            })}
            disabled={isPreviousDisabled}
            onClick={() => onChange(offset - limit, limit)}
          >
            <Trans>Previous</Trans>
          </button>

          {pages.map((page) => (
            <button
              key={page}
              className={classnames(styles.page, {
                [styles.activePage]: page === currentPage,
                [styles.disabled]: page < 0,
              })}
              disabled={page < 0}
              onClick={() => onChange((page - 1) * limit, limit)}
            >
              <Typography variant='button'>{page < 0 ? '...' : page}</Typography>
            </button>
          ))}

          <button
            className={classnames(styles.previousNext, {
              [styles.disabled]: isNextDisabled,
            })}
            disabled={isNextDisabled}
            onClick={() => onChange(offset + limit, limit)}
          >
            <Trans>Next</Trans>
          </button>
        </div>
      )}

      {paginationKey && !isOpenColumn && (
        <span className={styles.pagesControl}>
          <Typography variant='caption'>
            <Trans>View </Trans>
          </Typography>

          <div className={styles.dropdownWrapper}>
            <Dropdown
              variant='overlapping'
              options={dropdownOptions}
              handleChange={updatePageSize}
              selected={limit}
              trigger={<PagesTrigger limit={limit} />}
            />
          </div>

          <Typography variant='caption'>
            <Trans>items per page</Trans>
          </Typography>
        </span>
      )}
    </div>
  );
};

TablePagination.propTypes = {
  count: PropTypes.number,
  onChange: PropTypes.func,
  pageRangeDisplayed: PropTypes.number,
  marginPagesDisplayed: PropTypes.number,
  isPublic: PropTypes.bool,
};

TablePagination.defaultProps = {
  count: 0,
  onChange() {},
  pageRangeDisplayed: 0,
  marginPagesDisplayed: 0,
  isPublic: false,
};

export default memo(TablePagination);
