import React from 'react';

import { DefaultPageContainer } from '@components';

import SignUp from '../../components/SignUp';

const SHORT_TYPE_TO_LONG = {
  a: 'agency',
  c: 'client', // aka Company
};

const SignUpPage = ({ match: { params }, location: { state } }) => (
  <DefaultPageContainer
    title='Sign Up'
    colAttrs={{
      xs: 12,
      md: { size: 8, offset: 2 },
      lg: { size: 6, offset: 3 },
      xl: { size: 4, offset: 4 },
    }}
  >
    <SignUp
      type={params.shortType ? SHORT_TYPE_TO_LONG[params.shortType] : null}
      token={params.token}
      viaJob={params.viaJob}
      email={state ? state.email : null}
      agencyExists={state ? state.agencyExists : null}
    />
  </DefaultPageContainer>
);

export default SignUpPage;
