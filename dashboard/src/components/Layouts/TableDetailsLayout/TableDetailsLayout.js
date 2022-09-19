import React, { useState } from 'react';
import { Container, Row, Col } from 'reactstrap';
import { BiFullscreen, BiExitFullscreen } from 'react-icons/all';

import classNames from 'classnames';
import PropTypes from 'prop-types';

import styles from './TableDetailsLayout.module.scss';

const TableDetailsLayout = ({
  onClose,
  isOpen,
  header,
  renderTable,
  renderDetails,
  detailsClosedInnerWrapperClassName,
  detailsWrapperClassName,
  wrapperClassName,
}) => {
  const [isFullScreen, setIsFullScreen] = useState(false);

  const handleClose = () => {
    onClose();
    setIsFullScreen(false);
  };

  const closeRowStyles = classNames(detailsClosedInnerWrapperClassName, styles.isClose);
  const openRowStyles = styles.isOpen;

  return (
    <>
      {!isFullScreen && header}

      <div
        className={classNames({ [wrapperClassName]: !isFullScreen }, styles.wrapper)}
      >
        <Container>
          <Row
            className={classNames([
              styles.innerWrapper,
              { [styles.fixedWidth]: !isFullScreen },
              isOpen ? openRowStyles : closeRowStyles,
            ])}
          >
            {!isFullScreen && (
              <Col className={classNames(isOpen ? [styles.sidebar, 'sidebar'] : 'p-0')}>
                {renderTable({
                  // we use render function to explicitly pass props
                  areDetailsOpen: isOpen,
                  hideHeader: Boolean(isOpen),
                })}
              </Col>
            )}

            {isOpen && (
              <Col
                className={classNames([
                  styles.main,
                  detailsWrapperClassName,
                  'main-column',
                ])}
              >
                <div className={classNames([styles.controls])}>
                  <button
                    className={classNames([styles.iconButton, styles.fullscreen])}
                    onClick={() => setIsFullScreen(!isFullScreen)}
                  >
                    {isFullScreen ? <BiExitFullscreen /> : <BiFullscreen />}
                  </button>

                  <button
                    onClick={handleClose}
                    className={classNames([styles.iconButton, styles.close])}
                  />
                </div>

                {/*We use function to prevent it from rendering, if data isn't provided*/}
                {renderDetails()}
              </Col>
            )}
          </Row>
        </Container>
      </div>
    </>
  );
};

TableDetailsLayout.propTypes = {
  renderTable: PropTypes.func.isRequired,
  renderDetails: PropTypes.func.isRequired,
  header: PropTypes.node,
  wrapperClassName: PropTypes.string,
  detailsWrapperClassName: PropTypes.string,
  detailsClosedInnerWrapperClassName: PropTypes.string,
};

TableDetailsLayout.defaultProps = {
  isCandidates: false,
  header: null,
  renderDetails: null,
  wrapperClassName: '',
  detailsWrapperClassName: '',
  detailsClosedInnerWrapperClassName: '',
};

export default TableDetailsLayout;
