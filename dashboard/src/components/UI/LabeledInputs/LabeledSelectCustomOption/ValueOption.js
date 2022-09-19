import React from 'react';
import { components } from 'react-select';

import styles from './LabeledSelectCustomOption.module.scss';

const { SingleValue } = components;

const ValueOption = (props) => (
  <SingleValue {...props}>
    {props.data.icon && <div className={styles.icon}>{props.data.icon}</div>}
    <span className={styles.label}>{props.data.name}</span>
  </SingleValue>
);

export default ValueOption;
