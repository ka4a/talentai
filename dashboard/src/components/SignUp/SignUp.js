import React from 'react';
import { Redirect } from 'react-router';
import { Alert } from 'reactstrap';

import { Trans } from '@lingui/macro';

import SignUpCheckEmailForm from './SignUpCheckEmailForm';
import SignUpClientForm from './SignUpClientForm';
import SignUpAgencyForm from './SignUpAgencyForm';
import SignUpRecruiterForm from './SignUpRecruiterForm';

export default class SignUp extends React.Component {
  state = {
    created: false,
    message: '',
    type: null,
    email: null,
    agencyExists: null,
    redirect: null,
  };

  constructor(props) {
    super(props);

    this.state.type = props.type || null;
    this.state.email = props.email || null;
    this.state.agencyExists = props.agencyExists;

    const invalidProps =
      this.state.email &&
      (!this.state.type ||
        (this.state.type === 'agency' && this.state.agencyExists === null));

    if (invalidProps) {
      throw new Error('type and agencyExists are required if email is passed');
    }
  }

  onEmailChecked = ({ type, email, agencyExists }) => {
    const { redirectAfterEmailChecked, token, viaJob } = this.props;

    if (redirectAfterEmailChecked) {
      let pathname = `/${type[0]}/sign-up/`;

      if (token) {
        pathname += `invite/${token}`;
      } else if (viaJob) {
        pathname += `via/${viaJob}`;
      }

      this.setState({
        redirect: {
          pathname,
          state: { email, agencyExists },
        },
      });
    } else {
      this.setState({ type, email, agencyExists });
    }
  };

  onSaved = ({ message }) => {
    this.setState({ created: true, message });
  };

  render() {
    const { redirectAfterEmailChecked } = this.props;
    const { created, message, type, email, agencyExists, redirect } = this.state;

    if (redirect) {
      return <Redirect push to={redirect} />;
    }

    if (created) {
      return (
        <>
          <Alert color='info'>{message}</Alert>
        </>
      );
    }

    return (
      <>
        {!email ? (
          <>
            {!redirectAfterEmailChecked ? (
              <h1>
                <Trans>Sign Up</Trans>
              </h1>
            ) : null}
            <SignUpCheckEmailForm type={type} onChecked={this.onEmailChecked} />
          </>
        ) : null}

        {email ? (
          <>
            {type === 'client' ? (
              <>
                <h1>
                  <Trans>Sign Up as Company</Trans>
                </h1>
                <SignUpClientForm email={email} onSaved={this.onSaved} />
              </>
            ) : null}

            {type === 'agency' && !agencyExists ? (
              <>
                <h1>
                  <Trans>Sign Up as Agency</Trans>
                </h1>
                <SignUpAgencyForm
                  email={email}
                  token={this.props.token}
                  viaJob={this.props.viaJob}
                  onSaved={this.onSaved}
                />
              </>
            ) : null}
            {type === 'agency' && agencyExists ? (
              <>
                <h1>
                  <Trans>Sign Up as Recruiter</Trans>
                </h1>
                <SignUpRecruiterForm
                  email={email}
                  viaJob={this.props.viaJob}
                  onSaved={this.onSaved}
                />
              </>
            ) : null}
          </>
        ) : null}
      </>
    );
  }
}

SignUp.defaultProps = {
  redirectAfterEmailChecked: false,
  agencyExists: null,
};
