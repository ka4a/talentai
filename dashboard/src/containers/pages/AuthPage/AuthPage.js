import React, { memo, useCallback, useEffect, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { useHistory } from 'react-router';
import { useSelector } from 'react-redux';

import { t } from '@lingui/macro';

import { DefaultPageContainer, PageContainer } from '@components';
import { client } from '@client';
import { ZENDESK_URL } from '@constants';
import { fetchErrorHandler } from '@utils';

import {
  SignIn,
  ForgotPassword,
  SideInfo,
  SetNewPassword,
  Agreement,
} from './components';
import LoginInProgress from './components/LoginInProgress';

import styles from './AuthPage.module.scss';

const AuthPage = () => {
  const isAuthenticated = useSelector((state) => state.user.isAuthenticated);
  const isLegalAgreed = useSelector((state) => state.user.isLegalAgreed);

  const { pathname } = useLocation();
  const isZendeskSSORoute = useMemo(() => pathname.startsWith('/zendesk/'), [pathname]);

  const handleLogin = useLoginHandler(isZendeskSSORoute);

  const isAccessGranted = isAuthenticated && isLegalAgreed;

  useEffect(() => {
    if (isAccessGranted) handleLogin().catch(fetchErrorHandler);
  }, [isAccessGranted, handleLogin]);

  let page = useMemo(() => {
    if (isAccessGranted)
      return {
        title: 'Authenticating',
        content: <LoginInProgress />,
      };

    if (pathname.includes('login'))
      return {
        customTitle: true,
        title: t`Login`,
        content: <SignIn onLogin={handleLogin} />,
      };

    if (pathname.includes('agreement')) {
      return { title: t`Agreement`, content: <Agreement /> };
    }

    if (pathname.includes('restore-password')) {
      return { title: t`Restore Password`, content: <ForgotPassword /> };
    }

    if (pathname.includes('reset')) {
      return { title: t`Set New Password`, content: <SetNewPassword /> };
    }
  }, [pathname, handleLogin, isAccessGranted]);

  const UsedPageContainer = page.customTitle ? PageContainer : DefaultPageContainer;

  return (
    <UsedPageContainer title={page.title}>
      <div className={styles.wrapper}>
        <SideInfo />

        <div className={styles.content}>{page.content}</div>
      </div>
    </UsedPageContainer>
  );
};

function useLoginHandler(isZendeskSSORoute) {
  const { search } = useLocation();
  const history = useHistory();

  const redirectToHomePage = useCallback(() => {
    history.push('/');
    return Promise.resolve();
  }, [history]);

  const authenticateInZendesk = useCallback(async () => {
    const token = await getZendeskAccessToken();
    redirectToZendesk(token, search);
  }, [search]);

  return isZendeskSSORoute ? authenticateInZendesk : redirectToHomePage;
}

async function getZendeskAccessToken() {
  const response = await client.execute({
    operationId: 'zendesk_sso_jwt_token_retrieve',
  });
  return response?.obj?.token;
}

function redirectToZendesk(token, search) {
  const newSearch = search ? `${search}&jwt=${token}` : `?jwt=${token}`;
  window.location.href = `${ZENDESK_URL}/access/jwt${newSearch}`;
}

export default memo(AuthPage);
