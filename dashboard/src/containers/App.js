import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Route, Switch, useHistory, useLocation, matchPath } from 'react-router-dom';
import { toast } from 'react-toastify';

import { t } from '@lingui/macro';

import { fetchSwagger } from '@client';
import { readLocaleData, readUser, deauthenticateUser } from '@actions';
import { AuthenticatedRoute, AnonymousRoute, PublicRoute } from '@components';
import {
  AGENCY_GROUPS,
  AGENCY_ADMINISTRATORS,
  CLIENT_GROUPS,
  CLIENT_ADMINISTRATORS,
  CAREER_SITE_PATH,
} from '@constants';

import NavBar from '../components/NavBar';
import * as pages from './pages';
import {
  AgencyApprovalsRoutes,
  AgencyClientRoutes,
  CandidateRoutes,
  ClientAgenciesRoutes,
  JobRoutes,
  Popups,
  SettingsRoutes,
  SignupRoutes,
  ClientJobsRoutes,
  ZendeskLogoutRoute,
  UserRoutes,
} from './routes';

const ROUTES_WITHOUT_NAVBAR = [
  {
    path: `${CAREER_SITE_PATH}/:orgSlug`,
    component: pages.CareerSitePage,
  },
  {
    exact: true,
    path: '/jobs/:uuid',
    component: pages.PrivateJobPostingPage,
  },
];

const App = () => {
  const { pathname } = useLocation();

  const isHomePage = pathname === '/';

  const isRouteWithoutNavbar = ROUTES_WITHOUT_NAVBAR.some((path) =>
    matchPath(pathname, path)
  );

  const isAuthenticated = useSelector((state) => state.user.isAuthenticated);
  const isLegalAgreed = useSelector((state) => state.user.isLegalAgreed);
  const isDashboardUser = useSelector((state) => state.user.profile) !== null;

  const isLoading = useGetInitialData();

  useRedirects();

  // clear localStorage when logged out
  useEffect(() => {
    if (!isAuthenticated) localStorage.clear();
  }, [isAuthenticated]);

  const renderRoutes = !isHomePage && !isLoading;
  const shouldShowNavbar =
    isAuthenticated &&
    isDashboardUser &&
    isLegalAgreed &&
    !isRouteWithoutNavbar &&
    !isHomePage;

  return (
    <>
      {shouldShowNavbar && <NavBar />}

      <Popups />

      <PublicRoute exact path='/' component={pages.HomePage} />
      <PublicRoute exact path='/zendesk/logout' component={ZendeskLogoutRoute} />

      {renderRoutes && (
        <Switch>
          <PublicRoute path='/login' component={pages.AuthPage} exact />
          <PublicRoute path='/zendesk/login' component={pages.AuthPage} exact />
          <PublicRoute
            exact
            path='/legal_agreements/:type(privacy|terms)'
            component={pages.LegalAgreementFilePage}
          />
          <AuthenticatedRoute path='/agreement' component={pages.AuthPage} exact />
          <AnonymousRoute
            path={['/restore-password', '/reset/:uidb64/:token']}
            component={pages.AuthPage}
            exact
          />

          <PublicRoute
            exact
            path='/account/activate/:token'
            component={pages.ActivateAccountPage}
          />

          <Route path='/:shortType(a|c)/sign-up' component={SignupRoutes} />

          <Route path='/c/jobs' component={ClientJobsRoutes} />
          <Route path='/job/:jobId' component={JobRoutes} />

          {/* Candidate routes */}
          <AuthenticatedRoute
            path={['/candidates', '/candidate/:candidateId']}
            component={pages.CandidatesPage}
            exact
          />
          <AuthenticatedRoute
            key='candidate-add' // forces component recreation on redirect to edit page
            path={`/candidates/add`}
            component={pages.CandidateEditPage}
            exact
          />
          <Route path='/candidate/:candidateId' component={CandidateRoutes} />

          {/* User routes */}
          <Route path='/settings' component={SettingsRoutes} />

          <AuthenticatedRoute
            exact
            path='/notifications'
            component={pages.NotificationsPage}
          />

          {/*Users routes*/}
          <AuthenticatedRoute path='/users' component={UserRoutes} />

          {/* Public routes without navbar */}
          {ROUTES_WITHOUT_NAVBAR.map((route) => (
            <PublicRoute key={route.path} {...route} />
          ))}

          {/* Agency Routes */}
          <AuthenticatedRoute
            key='agency-dashboard'
            exact
            path='/a/jobs'
            groups={AGENCY_GROUPS}
            component={pages.AgencyDashboard}
          />

          <AuthenticatedRoute
            exact
            path='/a/clients'
            groups={AGENCY_GROUPS}
            component={pages.ClientsPage}
          />

          <Route path='/a/client/:clientId' component={AgencyClientRoutes} />

          <AuthenticatedRoute
            exact
            path='/a/proposal/:proposalId/placement'
            groups={AGENCY_GROUPS}
            component={pages.PlacementPage}
          />

          <AuthenticatedRoute
            exact
            path='/a/fee/:placementId'
            groups={AGENCY_GROUPS}
            component={pages.FeePage}
          />

          <Route path='/a/approvals' component={AgencyApprovalsRoutes} />

          {/* Client routes */}
          <AuthenticatedRoute
            key='invitations'
            exact
            path='/invitations/'
            groups={[CLIENT_ADMINISTRATORS, AGENCY_ADMINISTRATORS]}
            component={pages.InvitationsPage}
          />

          <AuthenticatedRoute
            key='client-analytics'
            exact
            path='/c/analytics'
            groups={[CLIENT_ADMINISTRATORS]}
            component={pages.AnalyticsPage}
          />

          <AuthenticatedRoute
            key='client-dashboard'
            exact
            path='/c/dashboard'
            groups={CLIENT_GROUPS}
            component={pages.ClientDashboard}
          />

          <Route path='/c/agencies' component={ClientAgenciesRoutes} />

          <AuthenticatedRoute
            exact
            path='/c/agency/:agencyId'
            groups={CLIENT_GROUPS}
            component={pages.AgencyPage}
          />

          {/* Public routes*/}

          <PublicRoute
            exact
            path='/confirm-interview/:publicUuid/'
            component={pages.CandidateConfirmation}
          />

          <PublicRoute component={pages.NotFoundPage} />
        </Switch>
      )}
    </>
  );
};

const useGetInitialData = () => {
  const [isLoading, setIsLoading] = useState(true);

  const isLoaded = useSelector((state) => state.user.isLoaded);
  const isAuthenticated = useSelector((state) => state.user.isAuthenticated);

  const dispatch = useDispatch();

  useEffect(() => {
    // start fetching swagger file
    fetchSwagger().catch(() => {
      setIsLoading(false);

      toast.error(t`An error occurred, please reload the page.`, {
        position: 'bottom-center',
        autoClose: false,
        className: 'toast-alert',
        closeOnClick: true,
      });
    });
  }, [dispatch]);

  useEffect(() => {
    dispatch(readLocaleData());

    // we deauthenticate non-auth users to finish loading
    if (isAuthenticated) dispatch(readUser()).catch(() => {});
    else dispatch(deauthenticateUser());

    if (isLoaded) setIsLoading(false);
  }, [dispatch, isLoaded, isAuthenticated]);

  return isLoading;
};

const useRedirects = () => {
  const history = useHistory();
  const { pathname } = useLocation();

  const isAuthenticated = useSelector((state) => state.user.isAuthenticated);
  const isLegalAgreed = useSelector((state) => state.user.isLegalAgreed);
  const isStaff = useSelector((state) => state.user.isStaff);
  const isDashboardUser = useSelector((state) => state.user.profile) !== null;

  useEffect(() => {
    if (isAuthenticated) {
      // redirect to agreement if not agreed
      if (!isLegalAgreed && !isStaff && isDashboardUser)
        return history.push('/agreement');

      // redirect to admin panel if this is superuser
      if (isStaff) window.location.pathname = '/admin/';
    }

    // need additional 'pathname' dependency here
  }, [pathname, history, isAuthenticated, isLegalAgreed, isStaff, isDashboardUser]);
};

export default App;
