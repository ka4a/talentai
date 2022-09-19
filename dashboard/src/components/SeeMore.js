import React, { useCallback, useState } from 'react';
import { Button } from 'reactstrap';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import styles from './SeeMore.module.css';

const SeeMore = React.memo(function SeeMore({ maxHeight, children }) {
  const [enabled, setEnabled] = useState(false);
  const [more, setMore] = useState(false);

  const measuredRef = useCallback(
    (node) => {
      if (node !== null) {
        setEnabled(node.getBoundingClientRect().height > maxHeight);
      } else {
        setEnabled(false);
      }
    },
    [maxHeight]
  );

  return (
    <>
      <div style={{ position: 'relative' }}>
        <div
          ref={measuredRef}
          style={
            !more && enabled
              ? {
                  maxHeight: `${maxHeight}px`,
                  overflowY: 'hidden',
                }
              : {}
          }
        >
          {children}
        </div>
        {!more && enabled ? <div className={styles.disappearing} /> : null}
      </div>

      {enabled ? (
        <div className='w-100 text-center'>
          {more ? (
            <Button className='btn-inv-secondary' onClick={() => setMore(false)}>
              <Trans>See Less</Trans>
            </Button>
          ) : (
            <Button className='btn-inv-primary' onClick={() => setMore(true)}>
              <Trans>See More</Trans>
            </Button>
          )}
        </div>
      ) : null}
    </>
  );
});

SeeMore.propTypes = {
  maxHeight: PropTypes.number.isRequired,
  children: PropTypes.node.isRequired,
};

export default SeeMore;
