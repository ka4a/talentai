import { defineMessage } from '@lingui/macro';

export const httpsReg = /((^http(s)?:\/\/)|^)/;

export const initialFormState = {
  // personal
  firstName: '',
  middleName: '',
  lastName: '',

  firstNameKanji: '',
  lastNameKanji: '',
  firstNameKatakana: '',
  lastNameKatakana: '',

  birthdate: null,
  nationality: '',
  gender: '',

  // contact
  email: '',
  secondaryEmail: '',
  phone: '',
  secondaryPhone: '',

  currentStreet: '',
  currentCity: '',
  currentPrefecture: '',
  currentPostalCode: '',
  currentCountry: '',

  linkedinUrl: '',
  githubUrl: '',
  websiteUrl: '',
  twitterUrl: '',

  // current employment
  currentPosition: '',
  currentCompany: '',

  currentSalaryCurrency: 'JPY',
  currentSalary: '',
  currentSalaryVariable: '',
  currentSalaryBreakdown: '',

  employmentStatus: '',
  taxEqualization: '',

  // skills & experience
  tags: [],
  languages: [],
  certifications: [],
  maxNumPeopleManaged: '',

  // candidate expectations
  salaryCurrency: 'JPY',
  salary: '',
  potentialLocations: '',
  otherDesiredBenefits: [],
  otherDesiredBenefitsOthersDetail: '',
  expectationsDetails: '',
  jobChangeUrgency: '',
  noticePeriod: '',

  // experience details
  experienceDetails: [],

  // education details
  educationDetails: [],

  // candidate management
  source: '',
  platform: '',
  sourceDetails: '',
  platformOtherDetails: '',
  owner: {},
  note: '',

  // attachments
  allResume: [],
  resumeError: null,

  photo: null,
  newPhoto: null,

  files: [],
  newFiles: [],
  filesError: null,

  scrapeData: true, // default true only if creating
};

export const SALARY_FIELDS = ['salary', 'currentSalary', 'currentSalaryVariable'];

export const SECTIONS = [
  { label: defineMessage({ message: 'Personal' }).id, id: 'personal-edit' },
  { label: defineMessage({ message: 'Contact' }).id, id: 'contact-edit' },
  {
    label: defineMessage({ message: 'Current Employment' }).id,
    id: 'current-employment-edit',
  },
  { label: defineMessage({ message: 'Skills & Experience' }).id, id: 'skills-edit' },
  {
    label: defineMessage({ message: 'Candidate Expectations' }).id,
    id: 'candidate-expectations-edit',
  },
  {
    label: defineMessage({ message: 'Experience Details' }).id,
    id: 'experience-details-edit',
  },
  {
    label: defineMessage({ message: 'Education Details' }).id,
    id: 'education-details-edit',
  },
  {
    label: defineMessage({ message: 'Candidate Management' }).id,
    id: 'candidate-management-edit',
  },
  { label: defineMessage({ message: 'Attachments' }).id, id: 'attachments-edit' },
  { label: defineMessage({ message: 'Metadata' }).id, id: 'metadata-edit' },
];
