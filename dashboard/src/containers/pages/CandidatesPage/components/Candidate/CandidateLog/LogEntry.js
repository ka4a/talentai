import React from 'react';

import _ from 'lodash';
import moment from 'moment';
import { Trans } from '@lingui/macro';

import LogFieldValue from './LogFieldValue';

import styles from './CandidateLog.module.scss';

export default function LogEntry(props) {
  const { changes = [], dateTime, actor } = props;

  if (changes.length === 0) {
    return null;
  }

  return (
    <li>
      <i className={styles.fa} />
      <div className={styles.timeLineItem}>
        <span className={styles.time}>{moment(dateTime).format('HH:mm')}</span>
        <div className={styles.timeLineHeader}>
          {_.map(changes, (value) => (
            <p key={value.name}>
              <Trans>
                The <strong>{FIELD_TITLES[value.name] || value.name}</strong> field was
                changed by <strong>{actor}</strong>
                {['photo'].includes(value.name) ? null : (
                  <>
                    {' '}
                    from{' '}
                    <strong>
                      <LogFieldValue value={value.old} name={value.name} />
                    </strong>{' '}
                    to{' '}
                    <strong>
                      <LogFieldValue value={value.new} name={value.name} />
                    </strong>
                  </>
                )}
              </Trans>
            </p>
          ))}
        </div>
      </div>
    </li>
  );
}

const FIELD_TITLES = {
  firstName: <Trans>First Name</Trans>,
  lastName: <Trans>Last Name(s)</Trans>,
  firstNameKanji: <Trans>First Name in Japanese</Trans>,
  lastNameKanji: <Trans>Last Name in Japanese</Trans>,
  email: <Trans>Email (Primary)</Trans>,
  phone: <Trans>Phone</Trans>,
  source: <Trans>Source</Trans>,
  currentCompany: <Trans>Current Employer</Trans>,
  currentLocation: <Trans>Current Location</Trans>,
  potentialLocations: <Trans>Potential Locations</Trans>,
  employmentStatus: <Trans>Employment Status</Trans>,
  linkedinUrl: <Trans>LinkedIn Profile</Trans>,
  githubUrl: <Trans>GitHub URL</Trans>,
  websiteUrl: <Trans>Personal Website URL</Trans>,
  twitterUrl: <Trans>Twitter URL</Trans>,
  summary: <Trans>Summary</Trans>,
  desiredEmploymentType: <Trans>Desired Employment Type</Trans>,
  desiredLocation: <Trans>Desired Location</Trans>,
  educationDetails: <Trans>Education Details</Trans>,
  experienceDetails: <Trans>Experience Details</Trans>,
  resume: <Trans>Resume</Trans>,
  photo: <Trans>Photo</Trans>,
  files: <Trans>Files</Trans>,
  salaryCurrency: <Trans>Salary Currency</Trans>,
  salary: <Trans>Salary</Trans>,
  reasonForJobChanges: <Trans>Reason for Job Changes</Trans>,
  languages: <Trans>Languages</Trans>,
  note: <Trans>Note</Trans>,
  tags: <Trans>Tags</Trans>,
  currentSalaryCurrency: <Trans>Current Salary Currency</Trans>,
  currentSalary: <Trans>Current Salary</Trans>,
  currentSalaryBreakdown: <Trans>Bonus Structure</Trans>,
  currentCountry: <Trans>Country</Trans>,
  skillDomain: <Trans>Skill Domain</Trans>,
  activator: <Trans>Activator</Trans>,
  leadConsultant: <Trans>Lead Consultant</Trans>,
  supportConsultant: <Trans>Support Consultant</Trans>,
  secondaryEmail: <Trans>Email (Secondary)</Trans>,
  currentPosition: <Trans>Current Job Title</Trans>,
  referredBy: <Trans>Referred By</Trans>,
  industry: <Trans>Industry</Trans>,
  department: <Trans>Department</Trans>,
  clientExpertise: <Trans>Client Expertise</Trans>,
  clientBrief: <Trans>Client Brief</Trans>,
  pushFactors: <Trans>Push Factors</Trans>,
  pullFactors: <Trans>Pull Factors</Trans>,
  companiesAlreadyAppliedTo: <Trans>Companies Already Applied To</Trans>,
  companiesAppliedTo: <Trans>Companies Applied To</Trans>,
  age: <Trans>Age</Trans>,
  nationality: <Trans>Nationality</Trans>,
  workMobile: <Trans>Phone number (Primary)</Trans>,
  workDirect: <Trans>Phone number (Secondary)</Trans>,
  isMet: <Trans>Is Met</Trans>,
  isClientContact: <Trans>Is Client Contact</Trans>,
  internalStatus: <Trans>Internal Status</Trans>,
  owner: <Trans>Owner</Trans>,
};
