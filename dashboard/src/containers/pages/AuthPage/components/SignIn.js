import React, { memo, useCallback, useState } from 'react';
import { useDispatch } from 'react-redux';

import { Trans, t } from '@lingui/macro';

import { loginUser, readLocaleData } from '@actions';
import {
  fetchErrorHandler,
  showSuccessToast,
  getErrorsInputInvalid,
  getErrorsInputFeedback,
} from '@utils';
import { Button, LabeledInput, Typography, WindowBackground } from '@components';

import styles from '../AuthPage.module.scss';

const SignIn = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const dispatch = useDispatch();

  const onSubmit = useCallback(async () => {
    setIsLoading(true);

    try {
      const { obj: user } = await dispatch(loginUser(email, password));
      // Part of redirects are handled in useRedirects hook in App.js
      if (user.isLegalAgreed) {
        await onLogin();

        dispatch(readLocaleData());

        showSuccessToast(
          <Trans>
            Welcome, {user.firstName} {user.lastName}
          </Trans>
        );
      }
    } catch (error) {
      fetchErrorHandler(error);
      setErrors(error.response?.obj || {});
      setIsLoading(false);
    }
  }, [dispatch, email, password, onLogin]);

  const handleKeyPress = useCallback(
    async (event) => {
      if (event.key === 'Enter') await onSubmit();
    },
    [onSubmit]
  );

  return (
    <WindowBackground className={styles.contentWrapper}>
      <Typography variant='h1' className={styles.contentHeader}>
        <Trans>Sign in</Trans>
      </Typography>

      <LabeledInput
        name='email'
        value={email}
        label={t`Email Address`}
        onChange={(e) => setEmail(e.target.value)}
        wrapperClassName={styles.input}
        tabIndex='1'
        isError={getErrorsInputInvalid(errors, 'email')}
      >
        {getErrorsInputFeedback(errors, 'email')}
      </LabeledInput>

      <LabeledInput
        value={password}
        label={t`Password`}
        onChange={(e) => setPassword(e.target.value)}
        onKeyPress={handleKeyPress}
        wrapperClassName={styles.input}
        name='password'
        type='password'
        tabIndex='2'
        isError={getErrorsInputInvalid(errors, 'password')}
      >
        {getErrorsInputFeedback(errors, 'password')}
      </LabeledInput>

      {errors?.detail && <p className={styles.error}>{errors.detail}</p>}

      <div className={styles.loginButtons}>
        <Button
          variant='text'
          isLink
          to='/restore-password'
          className={styles.forgotPasswordLink}
        >
          <Trans>Forgot password?</Trans>
        </Button>

        <Button onClick={onSubmit} disabled={isLoading}>
          <Trans>Sign In</Trans>
        </Button>
      </div>
    </WindowBackground>
  );
};

export default memo(SignIn);
