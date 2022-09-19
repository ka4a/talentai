import React from 'react';

import { render } from '@tests/customTestRender';

import Badge from './Badge';

it('renders with given text', () => {
  const { getByText } = render(<Badge text='success' />);
  expect(getByText('success')).toBeInTheDocument();
});
