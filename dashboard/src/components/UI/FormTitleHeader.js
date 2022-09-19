import React from 'react';

import FormHeader from '@components/UI/FormHeader';
import { Typography } from '@components';
import styles from '@styles/form.module.scss';

function FormTitleHeader({ children }) {
  return (
    <FormHeader>
      <Typography variant='h1' className={styles.title}>
        {children}
      </Typography>
    </FormHeader>
  );
}

export default FormTitleHeader;
