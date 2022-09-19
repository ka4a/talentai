import { defineMessage } from '@lingui/macro';

export const SECTIONS = [
  { label: defineMessage({ message: 'Details' }).id, id: 'settings-details' },
  { label: defineMessage({ message: 'Password' }).id, id: 'settings-password' },
  {
    label: defineMessage({ message: 'Email Notifications' }).id,
    id: 'settings-notifications',
  },
];

export const initialState = {
  oldPassword: '',
  newPassword: '',
  photo: null,
  newPhoto: null,
  isActive: false,
  notificationSettings: [],
  groups: [],
};
