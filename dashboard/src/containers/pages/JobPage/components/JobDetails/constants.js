import { defineMessage } from '@lingui/macro';

export const SECTIONS = [
  { label: defineMessage({ message: 'Details' }).id, id: 'job-details' },
  { label: defineMessage({ message: 'Requirements' }).id, id: 'job-requirements' },
  { label: defineMessage({ message: 'Job Conditions' }).id, id: 'job-conditions' },
  { label: defineMessage({ message: 'Hiring Process' }).id, id: 'job-hiring-process' },
  { label: defineMessage({ message: 'Attachments' }).id, id: 'job-attachments' },
  { label: defineMessage({ message: 'Metadata' }).id, id: 'job-metadata' },
];
