import React, { useState } from 'react';
import { Col, PopoverBody, UncontrolledPopover } from 'reactstrap';
import { MdInfoOutline } from 'react-icons/md';

import classnames from 'classnames';
import _ from 'lodash';

import styles from './AnalyticsBlock.module.css';

export default function AnalyticsBlock(props) {
  const {
    title,
    titleSizeSm = false,
    helpText,
    size = 6,
    height = '425px',
    childrenAboveChart,
    children,
    chartContainerStyles,
  } = props;

  // eslint-disable-next-line no-unused-vars
  const [elId, setElId] = useState(() => _.uniqueId('AnalyticsBlock'));

  return (
    <Col xs={12} md={size}>
      <div className={styles.helpContainer}>
        {helpText && (
          <>
            <div id={elId} className={`${styles.helpBlock} text-muted`}>
              <MdInfoOutline size='24px' />
            </div>
            <UncontrolledPopover trigger='hover' target={elId}>
              <PopoverBody className={styles.helpPopover}>{helpText}</PopoverBody>
            </UncontrolledPopover>
          </>
        )}

        <div className={styles.container} style={{ height }}>
          <div
            className={classnames(
              'font-weight-bold',
              { 'fs-18': titleSizeSm },
              { 'fs-24': !titleSizeSm }
            )}
          >
            {title}
          </div>
          {childrenAboveChart}
          <div className={styles.chartContainer} style={chartContainerStyles}>
            {children}
          </div>
        </div>
      </div>
    </Col>
  );
}
