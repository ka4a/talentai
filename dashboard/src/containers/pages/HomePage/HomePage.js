import React, { memo, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { useHistory } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { Redirect } from 'react-router-dom';
import { Alert, Col, Container, Row } from 'reactstrap';

import { Trans } from '@lingui/macro';

import { Loading, Button } from '@components';
import { useIsAuthenticatedByRoles } from '@hooks';
import { logoutUser } from '@actions';
import { AGENCY_GROUPS, CLIENT_GROUPS } from '@constants';

const HomePage = () => {
  const user = useSelector((state) => state.user);
  const { isLoaded, isAuthenticated, isActivated } = user;

  const isClient = useIsAuthenticatedByRoles(CLIENT_GROUPS);
  const isAgency = useIsAuthenticatedByRoles(AGENCY_GROUPS);

  const redirectPath = (() => {
    if (!isAuthenticated) return '/login';
    if (isClient) return '/c/jobs';
    if (isAgency) return '/a/jobs';
    return null;
  })();

  const history = useHistory();

  const dispatch = useDispatch();

  const logout = useCallback(async () => {
    await dispatch(logoutUser());
    history.push('/login');
  }, [dispatch, history]);

  if (!isLoaded) return <Loading className='mt-48' />;

  if (redirectPath) return <Redirect to={redirectPath} />;

  if (!isActivated) {
    return (
      <Container>
        <Row>
          <Col>
            <Alert color='info'>
              <Trans>Please check your email to activate your account.</Trans>
            </Alert>

            <Button variant='text' onClick={logout}>
              <Trans>Logout</Trans>
            </Button>
          </Col>
        </Row>
      </Container>
    );
  }

  return (
    <Container>
      <Row>
        <Col>
          <Alert color='info'>
            <Trans>Your account is pending approval.</Trans>
          </Alert>

          <Button variant='text' onClick={logout}>
            <Trans>Logout</Trans>
          </Button>
        </Col>
      </Row>
    </Container>
  );
};

export default memo(HomePage);
