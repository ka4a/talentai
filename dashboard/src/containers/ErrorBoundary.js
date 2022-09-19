import React, { Component } from 'react';
import { connect } from 'react-redux';
import { Alert, Button, Col, Container, Row } from 'reactstrap';
import { HiOutlineArrowLeft } from 'react-icons/hi';

import * as Sentry from '@sentry/react';

import { showErrorToast, ErrorBoundaryContext } from '@utils';
import ErrorToastContent from '@components/ErrorToastContent';
import { Typography } from '@components';

const isProduction = process.env.NODE_ENV === 'production';

class ErrorBoundary extends Component {
  state = { error: null, eventId: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  reportError = (error, info) => {
    if (isProduction) {
      Sentry.withScope((scope) => {
        const { user } = this.props;
        scope.setExtras(info);

        if (user) {
          const { id, email } = user;
          scope.setUser({ id, email });
        }

        const eventId = Sentry.captureException(error);
        this.setState({ eventId });
      });
    }
  };

  reportHandledError = (error, info) => {
    this.reportError(error, info);

    if (error.toast) {
      const { title, message } = error.toast;
      showErrorToast(<ErrorToastContent title={title} message={message} />);
    }
  };

  providedContext = {
    reportError: this.reportHandledError,
  };

  componentDidCatch(error, info) {
    this.reportError(error, info);
  }

  onReportFeedback = (e) => {
    e.preventDefault();
    Sentry.showReportDialog({
      eventId: this.state.eventId,
    });
  };

  render() {
    const { error, eventId } = this.state;
    const { children } = this.props;

    if (error) {
      return (
        <Container className='mt-8'>
          <Row>
            <Col xs={12}>
              <Alert color='danger'>
                <div>
                  <strong>An error has occurred</strong>
                </div>

                <div>
                  The development team has been notified and will look into the issue.
                  {eventId && ` (#${eventId})`}
                </div>

                {isProduction && eventId && (
                  <div>
                    <Button type='button' color='link' onClick={this.onReportFeedback}>
                      Report feedback
                    </Button>
                  </div>
                )}

                <div>
                  <a href='/'>
                    <Typography variant='caption'>
                      <HiOutlineArrowLeft /> Back to Home Screen
                    </Typography>
                  </a>
                </div>
              </Alert>
            </Col>
          </Row>
        </Container>
      );
    }

    return (
      <ErrorBoundaryContext.Provider value={this.providedContext}>
        {children}
      </ErrorBoundaryContext.Provider>
    );
  }
}

const mapStateToProps = (state) => ({ user: state.user });

export default connect(mapStateToProps)(ErrorBoundary);
