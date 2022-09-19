import React, { memo, useCallback, useMemo } from 'react';
import { batch, useDispatch, useSelector } from 'react-redux';

import classnames from 'classnames';
import { Trans } from '@lingui/macro';

import { setUser, updateUser } from '@actions';

import Dropdown from '../../../UI/Dropdown';
import Typography from '../../../UI/Typography';
import usePages from '../../hooks/usePages';
import PagesTrigger from '../PagesTrigger';

import styles from './TablePagination.module.scss';

const TablePagination = (props) => {
  const {
    count,
    offset,
    limit,
    pageRangeDisplayed,
    marginPagesDisplayed,
    onChange,
    paginationKey,
    isOpenColumn,
  } = props;

  const user = useSelector((state) => state.user);
  const paginationSchema = useSelector(
    (state) => state.settings.localeData.paginationSchema ?? []
  );

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
      batch(() => {
        dispatch(
          setUser({
            ...user,
            frontendSettings: {
              ...user.frontendSettings,
              [paginationKey]: id,
            },
          })
        );

        dispatch(
          updateUser({
            frontendSettings: {
              [paginationKey]: id,
            },
          })
        );
      });

      onChange(0, id);
    },
    [dispatch, onChange, paginationKey, user]
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
            className={classnames([
              styles.previousNext,
              { [styles.disabled]: isPreviousDisabled },
            ])}
            disabled={isPreviousDisabled}
            onClick={() => onChange(offset - limit, limit)}
          >
            <Trans>Previous</Trans>
          </button>

          {pages.map((p) => (
            <button
              key={p}
              className={classnames(styles.page, {
                [styles.activePage]: p === currentPage,
                [styles.disabled]: p < 0,
              })}
              disabled={p < 0}
              onClick={() => onChange((p - 1) * limit, limit)}
            >
              <Typography variant='button'>{p < 0 ? '...' : p}</Typography>
            </button>
          ))}

          <button
            className={classnames([
              styles.previousNext,
              { [styles.disabled]: isNextDisabled },
            ])}
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

export default memo(TablePagination);
