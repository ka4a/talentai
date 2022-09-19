import React, { memo } from 'react';

import { ShowAuthenticated } from '@components/auth';

import PersonalInfoSection from './sections/PersonalInfoSection';
import ContactSection from './sections/ContactSection';
import CurrentEmploymentSection from './sections/CurrentEmploymentSection';
import SkillsExperienceSection from './sections/SkillsExperienceSection';
import AttachmentsSection from './sections/AttachmentsSection';
import ExpectationsSection from './sections/ExpectationsSection';
import ExperienceDetailsSection from './sections/ExperienceDetailsSection';
import EducationDetailsSection from './sections/EducationDetailsSection';
import CandidateManagementSection from './sections/CandidateManagementSection';
import MetaDataSection from './sections/MetaDataSection';
import ApplicationsSection from './sections/ApplicationsSection';
import { ROLES_WITH_FULL_CANDIDATE_ACCESS } from './constants';

import styles from './CandidateDetailsSection.module.scss';

const CandidateDetailsTab = () => (
  <div className={styles.candidateDetailsWrapper}>
    <PersonalInfoSection />
    <ContactSection />
    <CurrentEmploymentSection />
    <SkillsExperienceSection />

    <ShowAuthenticated groups={ROLES_WITH_FULL_CANDIDATE_ACCESS}>
      <ExpectationsSection />
    </ShowAuthenticated>

    <ExperienceDetailsSection />
    <EducationDetailsSection />

    <ShowAuthenticated groups={ROLES_WITH_FULL_CANDIDATE_ACCESS}>
      <CandidateManagementSection />
    </ShowAuthenticated>

    <AttachmentsSection />
    <MetaDataSection />
    <ApplicationsSection />
  </div>
);

export default memo(CandidateDetailsTab);
