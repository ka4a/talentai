import React, { memo, useEffect, useRef, useState } from 'react';
import { useIntersection } from 'react-use';

import { Trans } from '@lingui/macro';
import PropTypes from 'prop-types';
import classnames from 'classnames';

import Button from '../Button';

import styles from './ButtonBar.module.scss';

const ButtonBar = (props) => {
  const {
    className,
    isDisabled,
    isSaveDisabled,
    shouldShowCancelButton,
    onSave,
    onCancel,
    customButtons,
    saveText,
    isModal,
  } = props;

  const [withShadow, setWithShadow] = useState(false);

  const barRef = useRef(null);

  const intersection = useIntersection(barRef, {
    threshold: [0, 1],
    rootMargin: '-30px',
  });

  useEffect(() => {
    if (intersection) {
      setWithShadow(intersection?.intersectionRatio === 0);
    }
  }, [intersection]);

  const shadowStyle = {
    [styles.withShadow]: withShadow,
    [styles.modal]: isModal,
  };

  return (
    <>
      <div className={classnames([styles.container, className, shadowStyle])}>
        {/* This block overlaps the form and emulates bottom margin
            Used only inside regular form (not inside modals) */}
        {withShadow && !isModal && (
          <>
            <div className={styles.backgroundWrapper} />
            <div className={classnames([styles.shadow, shadowStyle])} />
          </>
        )}

        <div className={classnames([styles.wrapper, shadowStyle])}>
          {customButtons ?? (
            <>
              {shouldShowCancelButton && (
                <Button
                  variant='secondary'
                  color='neutral'
                  onClick={onCancel}
                  disabled={isDisabled}
                >
                  <Trans>Cancel</Trans>
                </Button>
              )}

              <Button onClick={onSave} disabled={isDisabled || isSaveDisabled}>
                {saveText ?? <Trans>Save</Trans>}
              </Button>
            </>
          )}
        </div>
      </div>

      <div ref={barRef} className={styles.wrapperEdge} />
    </>
  );
};

ButtonBar.propTypes = {
  onSave: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  shouldShowCancelButton: PropTypes.bool,
  isDisabled: PropTypes.bool,
  isSaveDisabled: PropTypes.bool,
  className: PropTypes.string,
  customButtons: PropTypes.element,
  saveText: PropTypes.string,
  isModal: PropTypes.bool,
};

ButtonBar.defaultProps = {
  shouldShowCancelButton: true,
  isDisabled: false,
  isSaveDisabled: false,
  className: '',
  customButtons: null,
  saveText: null,
  isModal: false,
};

export default memo(ButtonBar);
