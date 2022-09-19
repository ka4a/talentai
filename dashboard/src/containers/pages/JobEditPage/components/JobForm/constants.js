import { defineMessage } from '@lingui/macro';

import { AGENCY_ADMINISTRATORS, AGENCY_MANAGERS, TALENT_ASSOCIATES } from '@constants';

export const USERS_ALLOWED_TO_CHANGE_STATUS = [
  TALENT_ASSOCIATES,
  AGENCY_ADMINISTRATORS,
  AGENCY_MANAGERS,
];

export const SECTIONS = [
  { label: defineMessage({ message: 'Details' }).id, id: 'details-edit' },
  { label: defineMessage({ message: 'Requirements' }).id, id: 'requirements-edit' },
  { label: defineMessage({ message: 'Job Conditions' }).id, id: 'job-conditions-edit' },
  { label: defineMessage({ message: 'Hiring Process' }).id, id: 'hiring-process-edit' },
  { label: defineMessage({ message: 'Attachments' }).id, id: 'attachments-edit' },
  { label: defineMessage({ message: 'Metadata' }).id, id: 'metadata-edit' },
];

export const initialFormState = {
  // details
  title: '',
  function: '',
  department: '',
  employmentType: '',
  reasonForOpening: '',
  mission: '',
  responsibilities: '',
  targetHiringDate: '',

  // requirements
  requirements: '',
  educationalLevel: '',
  workExperience: '',
  skills: [],
  requiredLanguages: [],

  // job conditions
  salaryFrom: '',
  salaryTo: '',
  salaryPer: 'year',
  salaryCurrency: 'JPY',
  bonusSystem: '',
  probationPeriodMonths: '',
  workLocation: '',
  workingHours: '',
  breakTimeMins: '',
  flexitimeEligibility: '',
  teleworkEligibility: '',
  overtimeConditions: '',
  paidLeaves: '',
  additionalLeaves: '',
  socialInsurances: [],
  commutationAllowance: '',
  otherBenefits: [],

  // hiring process
  managers: [],
  openingsCount: 1,
  status: 'open',
  recruiters: [],
  hiringCriteria: [],
  questions: [],
  interviewTemplates: [],
  hiringProcess: '',

  // attachments
  files: [],
  newFiles: [],

  // metadata
  id: '',
  createdAt: null,
  closedAt: null,
  publishedAt: null,
  updatedAt: null,
  owner: null,

  country: 'jp',
  agencies: [],
};
