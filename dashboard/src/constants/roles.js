import { defineMessage } from '@lingui/macro';

export const TALENT_ASSOCIATES = 'Talent Associates';
export const HIRING_MANAGERS = 'Hiring Managers';
export const CLIENT_ADMINISTRATORS = 'Client Administrators';
export const CLIENT_INTERNAL_RECRUITERS = 'Client Internal Recruiters';
export const CLIENT_STANDARD_USERS = 'Client Standard Users';

export const AGENCY_ADMINISTRATORS = 'Agency Administrators';
export const AGENCY_MANAGERS = 'Agency Managers';
export const RECRUITERS = 'Recruiters';

export const CLIENT_GROUPS = [
  TALENT_ASSOCIATES,
  HIRING_MANAGERS,
  CLIENT_ADMINISTRATORS,
  CLIENT_INTERNAL_RECRUITERS,
  CLIENT_STANDARD_USERS,
];
export const AGENCY_GROUPS = [AGENCY_ADMINISTRATORS, AGENCY_MANAGERS, RECRUITERS];

export const GROUP_TO_ROLE_NAME_MAP = {
  [CLIENT_ADMINISTRATORS]: defineMessage({ message: 'Administrator' }).id,
  [CLIENT_INTERNAL_RECRUITERS]: defineMessage({ message: 'Internal Recruiter' }).id,
  [CLIENT_STANDARD_USERS]: defineMessage({ message: 'Standard User' }).id,
  // Rest not used at the moment, but better to map them
  [TALENT_ASSOCIATES]: defineMessage({ message: 'Talent Associate' }).id,
  [HIRING_MANAGERS]: defineMessage({ message: 'Hiring Manager' }).id,

  [AGENCY_ADMINISTRATORS]: defineMessage({ message: 'Administrator' }).id,
  [AGENCY_MANAGERS]: defineMessage({ message: 'Manager' }).id,
  [RECRUITERS]: defineMessage({ message: 'Recruiter' }).id,
};

const getRoleChoices = (availableRoleValues) =>
  availableRoleValues.map((value) => ({
    value,
    name: GROUP_TO_ROLE_NAME_MAP[value],
  }));

export const ROLE_CHOICES = {
  client: getRoleChoices([
    CLIENT_ADMINISTRATORS,
    CLIENT_INTERNAL_RECRUITERS,
    CLIENT_STANDARD_USERS,
  ]),
  agency: getRoleChoices([AGENCY_ADMINISTRATORS, AGENCY_MANAGERS, RECRUITERS]),
};
