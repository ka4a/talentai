import React, { memo, useCallback, useEffect, useRef, useState } from 'react';
import { useLockBodyScroll } from 'react-use';
import { useDispatch } from 'react-redux';
import ModalRM from 'react-modal';

// ResizeObserver is not supported before Safari v14
import ResizeObserver from 'resize-observer-polyfill';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { setIsScrollStart } from '@actions';

import ButtonBar from '../ButtonBar';
import Typography from '../Typography';

import styles from './Modal.module.scss';

const WIDTH_SIZES = {
  small: 400,
  medium: 640,
  large: 740,
  huge: 975,
};

const Modal = (props) => {
  const {
    isOpen,
    isSaveDisabled,
    onClose,
    title,
    onCancel,
    onSave,
    saveText,
    children,
    size,
    withFooter,
    withoutOverflow,
    withoutAnimation,
    onAfterClose: onAfterCloseOuter,
    customButtons,
    ...rest
  } = props;

  useLockBodyScroll(isOpen);

  const { observer, isEnd, handleScroll } = useContentScroll();

  const onCancelInner = useCallback(() => {
    onCancel();
    onClose();
  }, [onCancel, onClose]);

  const onAfterClose = useCallback(() => {
    onAfterCloseOuter();

    /**
     * This is workaround for issue when double press ESC
     * In that case ReactModal__Body--open class is not removed automatically
     * Delay is needed until DOM changes are applied
     */
    setTimeout(() => {
      const modals = document.querySelectorAll('.ReactModalPortal');
      if (!modals.length) document.body.classList.remove('ReactModal__Body--open');
    });
  }, [onAfterCloseOuter]);

  const maxWidth = WIDTH_SIZES[size];

  return (
    <ModalRM
      isOpen={isOpen}
      onRequestClose={onClose}
      onAfterClose={onAfterClose}
      className={classnames([
        styles.container,
        { [styles.withoutOverflow]: withoutOverflow },
      ])}
      overlayClassName={styles.overlay}
      style={{ content: { maxWidth } }}
      closeTimeoutMS={withoutAnimation ? 0 : 200} // transition timeout
      {...rest}
    >
      <div
        className={classnames([
          styles.wrapper,
          { [styles.withoutOverflow]: withoutOverflow },
        ])}
      >
        <div className={styles.header}>
          <Typography variant='h2'>{title}</Typography>
        </div>

        <div
          ref={(ref) => {
            // Observe the scrollingElement for when the content gets resized
            if (ref) observer.observe(ref);
          }}
          onScroll={handleScroll}
          className={classnames([
            styles.contentWrapper,
            { [styles.withoutFooter]: !withFooter },
          ])}
        >
          {children}
        </div>

        {withFooter && (
          <ButtonBar
            className={classnames({ [styles.withShadow]: !isEnd })}
            onSave={onSave}
            onCancel={onCancelInner}
            shouldShowCancelButton={Boolean(onCancel)}
            customButtons={customButtons}
            saveText={saveText}
            isSaveDisabled={isSaveDisabled}
            isModal
          />
        )}
      </div>
    </ModalRM>
  );
};

const useContentScroll = () => {
  const [isStart, setIsStart] = useState(true);
  const [isEnd, setIsEnd] = useState(true);

  /**
   * Observer tracks when modal's content size is changed.
   * When it changes we trigger scroll event on that object
   * in order to add/remove ButtonBar border
   */
  const observer = useRef(
    new (window.ResizeObserver ?? ResizeObserver)((entries) => {
      const element = entries[0].target.children[0];

      if (!element) return;

      const { scrollTop, scrollHeight, clientHeight } = element;
      if (scrollTop === 0 && scrollHeight === clientHeight) {
        setIsEnd(true);
        return;
      }

      // trigger scroll event and return scroll back to top
      element.scrollTo(0, 1);
      element.scrollTo(0, 0);
    })
  );

  const handleScroll = useCallback(
    (event) => {
      const { scrollTop, clientHeight, scrollHeight } = event.target;

      const isStartNew = scrollTop === 0;
      if (isStart !== isStartNew) setIsStart(isStartNew);

      const isEndNew = scrollHeight - scrollTop === clientHeight;
      if (isEnd !== isEndNew) setIsEnd(isEndNew);
    },
    [isEnd, isStart]
  );

  const dispatch = useDispatch();

  // set isStart to store in order to be able to get it in Modal's children
  useEffect(() => {
    dispatch(setIsScrollStart(isStart));
  }, [dispatch, isStart]);

  useEffect(() => {
    // Unobserve on unmount
    const element = observer.current;
    return () => {
      element.disconnect();
    };
  }, []);

  return {
    observer: observer.current,
    isEnd,
    handleScroll,
  };
};

Modal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  isSaveDisabled: PropTypes.bool,
  onClose: PropTypes.func,
  title: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  children: PropTypes.node,
  size: PropTypes.oneOf(Object.keys(WIDTH_SIZES)),
  onSave: PropTypes.func,
  onCancel: PropTypes.func,
  onAfterClose: PropTypes.func,
  withFooter: PropTypes.bool,
  withoutAnimation: PropTypes.bool,
  withoutOverflow: PropTypes.bool,
  customButtons: PropTypes.element,
  saveText: PropTypes.string,
};

Modal.defaultProps = {
  onSave: () => {},
  onClose: () => {},
  isSaveDisabled: false,
  onCancel: null,
  size: 'medium',
  withFooter: true,
  title: '',
  children: null,
  onAfterClose: () => {},
  withoutAnimation: false,
  withoutOverflow: false,
  customButtons: undefined,
  saveText: undefined,
};

export default memo(Modal);
