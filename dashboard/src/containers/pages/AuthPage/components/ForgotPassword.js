import React, { memo, useCallback, useState } from 'react';

import { useLingui } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { client } from '@client';
import { fetchErrorHandler } from '@utils';
import { Typography, LabeledInput, Button, WindowBackground } from '@components';

import InstructionsSent from './InstructionsSent';

import styles from '../AuthPage.module.scss';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [isLinkSent, setIsLinkSent] = useState(false);

  const { i18n } = useLingui();

  const onSubmit = useCallback(async () => {
    try {
      await client.execute({
        operationId: 'user_reset_password',
        parameters: { data: { email } },
      });

      setIsLinkSent(true);
    } catch (error) {
      fetchErrorHandler(error);
    }
  }, [email]);

  if (isLinkSent) return <InstructionsSent email={email} />;

  return (
    <WindowBackground className={styles.contentWrapper}>
      <Typography variant='h1' className={styles.contentHeader}>
        <Trans>Restore Password</Trans>
      </Typography>

      <LabeledInput
        name='email'
        value={email}
        label={i18n._(t`Email Address`)}
        onChange={(e) => setEmail(e.target.value)}
        wrapperClassName={styles.input}
      />

      <Button onClick={onSubmit} className={styles.submitButton}>
        <Trans>Send Me Instructions</Trans>
      </Button>
    </WindowBackground>
  );
};

export default memo(ForgotPassword);
