import React from 'react';
import { Alert } from 'reactstrap';
import { withRouter } from 'react-router';
import { connect } from 'react-redux';
import { Link } from 'react-router-dom';

import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { client } from '@client';
import { readUser } from '@actions';
import { DefaultPageContainer, ReqStatus } from '@components';
import { fetchLoadingWrapper, getDefaultReqState } from '@components/ReqStatus';

const mapDispatchToProps = (dispatch) => ({
  readUser: () => dispatch(readUser()),
});

class ActivateAccountPage extends React.Component {
  state = {
    ...getDefaultReqState(),
    activated: false,
    message: '',
  };

  activateAccount = fetchLoadingWrapper(() => {
    const { token } = this.props.match.params;

    return client
      .execute({
        operationId: 'user_activate',
        parameters: { data: { token } },
      })
      .then((response) => {
        this.setState({
          activated: true,
          message: response.obj.detail,
        });

        if (this.props.user.isAuthenticated) {
          this.props.readUser();
        }
      });
  }).bind(this);

  componentDidMount() {
    if (this.props.user.isActivated) {
      window.location.pathname = '/';
    } else {
      this.activateAccount();
    }
  }

  render() {
    const { user } = this.props;
    const { activated, message, reqStatus } = this.state;

    if (reqStatus.render) {
      return <ReqStatus {...reqStatus} />;
    }

    return (
      <DefaultPageContainer
        title={this.props.i18n._(t`Account Activation`)}
        colAttrs={{ md: { size: 4, offset: 4 } }}
      >
        {activated ? (
          <Alert color='info'>
            <div>{message}</div>
            <div>
              {user.isAuthenticated ? (
                <Link to='/'>
                  <Trans>Continue</Trans>
                </Link>
              ) : (
                <Link to='/login/'>
                  <Trans>Login</Trans>
                </Link>
              )}
            </div>
          </Alert>
        ) : null}
      </DefaultPageContainer>
    );
  }
}

export default withRouter(
  connect(null, mapDispatchToProps)(withI18n()(ActivateAccountPage))
);
