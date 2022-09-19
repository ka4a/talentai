import React from 'react';
import { components } from 'react-select';

import styles from './LabeledSelectCustomOption.module.scss';

const { Option } = components;

const IconOption = (props) => (
  <Option {...props}>
    {props.data.icon && <div className={styles.icon}>{props.data.icon}</div>}
    <span className={styles.label}>{props.data.name}</span>
  </Option>
);

export default IconOption;
