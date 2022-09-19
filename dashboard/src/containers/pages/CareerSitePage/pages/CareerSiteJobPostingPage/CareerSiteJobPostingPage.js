import React, { memo } from 'react';
import { useParams } from 'react-router-dom';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';

import { ReqStatus } from '@components';
import { useCareerSitePostingsRead } from '@swrAPI';

import CareerSitePageContainer from '../../components/CareerSitePageContainer';
import BackNavButton from '../../components/BackNavButton';
import JobPostingPageContent, { POSTING_TYPES } from '../../../JobPostingPageContent';

const CareerSiteJobPostingPage = ({ orgName, orgSlug }) => {
  const { jobSlug } = useParams();

  const { data: jobPosting, loading, error } = useCareerSitePostingsRead(
    orgSlug,
    jobSlug
  );

  if (!jobPosting || error) return <ReqStatus loading={loading} error={error} />;

  return (
    <CareerSitePageContainer title={jobPosting.title} orgName={orgName}>
      <JobPostingPageContent
        postingType={POSTING_TYPES.careerSite}
        jobPosting={jobPosting}
        backNavButton={
          <BackNavButton link={`/career/${orgSlug}`} linkText={t`Back to Job List`} />
        }
      />
    </CareerSitePageContainer>
  );
};

CareerSiteJobPostingPage.propTypes = {
  orgName: PropTypes.string,
  orgSlug: PropTypes.string.isRequired,
};

CareerSiteJobPostingPage.defaultProps = {
  orgName: '',
};

export default memo(CareerSiteJobPostingPage);
