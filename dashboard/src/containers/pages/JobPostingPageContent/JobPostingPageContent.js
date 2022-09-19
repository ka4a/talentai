import React, { useState } from 'react';
import { useBoolean } from 'react-use';

import PropTypes from 'prop-types';
import { defineMessage } from '@lingui/macro';
import classnames from 'classnames';

import { SectionsMenu, WindowBackground } from '@components';

import ApplicationSubmitted from './components/JobPostingApplicationSubmitted';
import {
  Details,
  JobConditions,
  Requirements,
} from '../JobPage/components/JobDetailsSections';
import ApplicationForm from './components/JobPostingApplicationForm';
import JobPostingHeader from './components/JobPostingHeader';

import styles from './JobPostingPageContent.module.scss';

function JobPostingPageContent({ jobPosting, backNavButton, postingType }) {
  const [isApplicationSubmitted, toggleIsApplicationSubmitted] = useBoolean(false);
  const [submittedEmail, setSubmittedEmail] = useState('');

  return (
    <>
      <JobPostingHeader
        job={jobPosting}
        shouldShowApply={!isApplicationSubmitted}
        shouldShowSalary
        backNavButton={backNavButton}
      />

      {isApplicationSubmitted ? (
        <ApplicationSubmitted email={submittedEmail} />
      ) : (
        <div className={styles.wrapper}>
          <div>
            <WindowBackground className={styles.formContainerWidePadded}>
              <Details job={jobPosting} />
              <Requirements isPosting job={jobPosting} />
              <JobConditions job={jobPosting} />
            </WindowBackground>

            <WindowBackground
              className={classnames(
                styles.formContainerWidePadded,
                styles.applicationContainer
              )}
            >
              <ApplicationForm
                jobPosting={jobPosting}
                showSuccessBox={toggleIsApplicationSubmitted}
                setSubmittedEmail={setSubmittedEmail}
                postingType={postingType}
              />
            </WindowBackground>
          </div>

          <SectionsMenu sections={SECTIONS} />
        </div>
      )}
    </>
  );
}

const SECTIONS = [
  { label: defineMessage({ message: 'Details' }).id, id: 'job-details' },
  { label: defineMessage({ message: 'Requirements' }).id, id: 'job-requirements' },
  { label: defineMessage({ message: 'Job Conditions' }).id, id: 'job-conditions' },
  { label: defineMessage({ message: 'Application' }).id, id: 'application' },
];

export const POSTING_TYPES = {
  private: 'private_posting',
  careerSite: 'career_site_posting',
};

JobPostingPageContent.propTypes = {
  jobPosting: PropTypes.object.isRequired,
  postingType: PropTypes.oneOf(Object.values(POSTING_TYPES)),
  backNavButton: PropTypes.node,
};

JobPostingPageContent.defaultProps = {
  backNavButton: null,
};

export default JobPostingPageContent;
