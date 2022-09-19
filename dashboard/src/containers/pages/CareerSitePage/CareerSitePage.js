import React from 'react';
import { Route, Switch } from 'react-router-dom';
import { useSelector } from 'react-redux';

import * as PropTypes from 'prop-types';
import useSWR from 'swr';

import { PublicOrgTopBar, ReqStatus } from '@components';
import { getLocalizedField } from '@utils';

import CareerSiteJobPostingListPage from './pages/CareerSiteJobPostingListPage/CareerSiteJobPostingListPage';
import CareerSiteJobPostingPage from './pages/CareerSiteJobPostingPage/CareerSiteJobPostingPage';

const CareerSitePage = ({ match }) => {
  const { orgSlug } = match.params;
  const orgSWR = useOrganizationSWR(orgSlug);
  const locale = useSelector(({ settings }) => settings.locale);

  if (!orgSWR.data) return <ReqStatus loading={!orgSWR.error} error={orgSWR.error} />;

  const org = orgSWR.data;

  const localizedOrgName = getLocalizedField(org, 'name', locale);

  return (
    <>
      <PublicOrgTopBar title={localizedOrgName} logo={org.logo} />
      <Switch>
        <Route exact path={`${match.path}/:jobSlug/`}>
          <CareerSiteJobPostingPage orgName={localizedOrgName} orgSlug={orgSlug} />
        </Route>
        <Route exact path={match.path}>
          <CareerSiteJobPostingListPage
            basePath={match.url}
            orgName={localizedOrgName}
            orgSlug={orgSlug}
          />
        </Route>
      </Switch>
    </>
  );
};

CareerSitePage.propTypes = {
  match: PropTypes.shape({
    path: PropTypes.string,
    params: PropTypes.shape({
      orgSlug: PropTypes.string,
    }),
  }).isRequired,
};

function useOrganizationSWR(orgSlug) {
  return useSWR(`public/career_site/organization/${orgSlug}`);
}

export default CareerSitePage;
