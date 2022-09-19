import React from 'react';

import PropTypes from 'prop-types';

import { joinTitle } from '@components/UI/pageContainers/utils';
import { PageContainer } from '@components';

function CareerSitePageContainer({ children, orgName, title }) {
  const fullTitle = joinTitle([title, orgName]);

  return <PageContainer title={fullTitle}>{children}</PageContainer>;
}

CareerSitePageContainer.propTypes = {
  orgName: PropTypes.string,
  title: PropTypes.string,
};

CareerSitePageContainer.defaultPage = {
  orgName: '',
  title: '',
};

export default CareerSitePageContainer;
