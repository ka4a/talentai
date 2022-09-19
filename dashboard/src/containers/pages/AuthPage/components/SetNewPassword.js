import React, { memo, useCallback, useState } from 'react';
import { Redirect, useHistory, useParams } from 'react-router-dom';
import { useSelector } from 'react-redux';

import { Trans, t } from '@lingui/macro';

import { Button, LabeledInput, Typography, WindowBackground } from '@components';
import {
  fetchErrorHandler,
  getErrorsInputFeedback,
  getErrorsInputInvalid,
} from '@utils';
import { client } from '@client';

import styles from '../AuthPage.module.scss';

const SetNewPassword = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});

  const isAuthenticated = useSelector((state) => state.user.isAuthenticated);

  const { uidb64, token } = useParams();
  const history = useHistory();

  const onSubmit = useCallback(async () => {
    try {
      await client.execute({
        operationId: 'user_confirm_password_reset',
        parameters: {
          data: {
            uidb64,
            token,
            newPassword1: password,
            newPassword2: confirmPassword,
          },
        },
      });

      history.push('/login');
    } catch (error) {
      if (error?.response?.status === 400) {
        setErrors(error.response.obj);
      } else {
        fetchErrorHandler(error);
      }
    }
  }, [confirmPassword, history, password, token, uidb64]);

  if (isAuthenticated) return <Redirect to='/' />;

  return (
    <WindowBackground className={styles.contentWrapper}>
      <Typography variant='h1' className={styles.contentHeader}>
        <Trans>Set New Password</Trans>
      </Typography>

      <LabeledInput
        value={password}
        label={t`Password`}
        onChange={(e) => setPassword(e.target.value)}
        wrapperClassName={styles.input}
        name='password'
        type='password'
        tabIndex='1'
        isError={getErrorsInputInvalid(errors, 'newPassword2')}
      >
        {getErrorsInputFeedback(errors, 'newPassword2')}
      </LabeledInput>

      <LabeledInput
        value={confirmPassword}
        label={t`Confirm Password`}
        onChange={(e) => setConfirmPassword(e.target.value)}
        wrapperClassName={styles.input}
        name='password'
        type='password'
        tabIndex='2'
      />

      <Button onClick={onSubmit} className={styles.submitButton}>
        <Trans>Change Password</Trans>
      </Button>
    </WindowBackground>
  );
};

export default memo(SetNewPassword);
