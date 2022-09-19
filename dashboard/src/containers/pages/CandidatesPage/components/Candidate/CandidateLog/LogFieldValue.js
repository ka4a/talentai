import React, { useState } from 'react';
import { Button, PopoverBody, UncontrolledPopover } from 'reactstrap';

import _ from 'lodash';

import LabeledRichEditor from '@components/UI/LabeledInputs/LabeledRichEditor';

import styles from './LogFieldValue.module.scss';

const DELAY = { show: 0, hide: 180 };

export default function LogFieldValue({ value, name }) {
  const [id] = useState(_.uniqueId('value-'));

  if (['clientBrief', 'note', 'currentSalaryBreakdown', 'summary'].includes(name)) {
    return (
      <>
        <Button id={id} color='link' className='p-0 h-100'>
          ...
        </Button>
        <UncontrolledPopover
          popperClassName={styles.valuePopper}
          boundariesElement='window'
          flip={false}
          target={id}
          placement='top'
          trigger='focus'
          delay={DELAY}
        >
          <PopoverBody>
            <LabeledRichEditor value={value} readOnly />
          </PopoverBody>
        </UncontrolledPopover>
      </>
    );
  }
  return <span>{['', null].includes(value) ? 'None' : String(value)}</span>;
}
