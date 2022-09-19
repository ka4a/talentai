import React, { useCallback, useMemo, memo, useRef } from 'react';
import { useHistory, useParams } from 'react-router-dom';
import { useHoverDirty } from 'react-use';

import classnames from 'classnames';

import TableCell from './TableCell';

import styles from './TableRow.module.scss';

const TableRow = (props) => {
  const {
    row,
    columns,
    rowClasses,
    getLink,
    shouldOpenTab,
    onClick,
    isOpenColumn,
  } = props;

  let currentId = useParams();
  const history = useHistory();

  const rowRef = useRef(null);
  const isHovering = useHoverDirty(rowRef);

  const link = useMemo(() => {
    if (!getLink) return null;
    const link = getLink(row);

    if (!link) return null;
    return link.pathname ? link : { pathname: link };
  }, [getLink, row]);

  const handleClick = useCallback(
    (e) => {
      if (onClick) onClick(e, row);

      if (!link) return;

      const shouldOpenLinkInNewTab =
        e.button === 1 || // middle mouse key click
        (e.metaKey && e.button === 0) || // left mouse key click with command key
        shouldOpenTab;

      if (shouldOpenLinkInNewTab) {
        window.open(link.pathname, '_blank');
      } else if (e.button === 0) {
        history.push(link.pathname, link.state);
      }
    },
    [link, history, shouldOpenTab, onClick, row]
  );

  const isActive =
    +currentId.candidateId === row.id || +currentId.proposalId === row.id;

  return (
    <tr
      ref={rowRef}
      onClick={handleClick}
      className={classnames(rowClasses?.(row) ?? '', {
        [styles.rowHover]: isHovering,
        [styles.isActive]: isActive,
      })}
    >
      {columns.map((col, i) => {
        if (isOpenColumn && col?.hideInSidebar) return null;

        return <TableCell key={i} col={col} row={row} link={link} />;
      })}
    </tr>
  );
};

export default memo(TableRow);
