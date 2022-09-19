import React, { memo, PureComponent } from 'react';

import _ from 'lodash';
import PropTypes from 'prop-types';

import { getErrorTextFromFetchError, showErrorToast } from '@utils';
import { client } from '@client';

import NotFoundPage from '../../containers/pages/NotFoundPage';
import Loading from '../UI/Loading';

export function getDefaultReqState(key = 'reqStatus') {
  return { [key]: { render: true, loading: false, error: null } };
}

function getErrorState(key, error) {
  return {
    [key]: {
      render: true,
      loading: false,
      errorObj: error,
      error: getErrorTextFromFetchError(error),
    },
  };
}

export function fetchLoadingWrapper(origGetPromises, key = 'reqStatus') {
  return _.wrap(origGetPromises, function (getPromises) {
    const promises = _.castArray(getPromises());

    this.setState({ [key]: { render: true, loading: true, error: null } }, () => {
      Promise.all(promises)
        .then(() => {
          this.setState({ [key]: { render: false, loading: false, error: null } });
        })
        .catch((error) => {
          this.setState(getErrorState(key, error));
        });
    });
  });
}

const ReqStatus = (props) => {
  const { loading, error, inline = false } = props;

  if (loading) return <Loading />;

  if (error) {
    if (error.statusCode === 404 || error?.response?.status === 404) {
      return <NotFoundPage inline={inline} />;
    } else {
      showErrorToast(getErrorTextFromFetchError(error));
      return null;
    }
  } else {
    return <></>;
  }
};

ReqStatus.propTypes = {
  loading: PropTypes.bool,
  error: PropTypes.any,
  inline: PropTypes.bool,
};

export default memo(ReqStatus);

export function withReqStatus(Component) {
  class WrappedComponent extends PureComponent {
    state = {
      render: true,
      loading: false,
      error: null,
    };

    execute = async (data) => {
      this.setState({ render: true, loading: true, error: null });
      try {
        const response = await client.execute(data);
        this.setState({ render: false, loading: false, error: null });
        return response;
      } catch (error) {
        this.setState({
          render: true,
          loading: false,
          error: getErrorTextFromFetchError(error),
        });
        throw error;
      }
    };

    renderIfLoaded = (render) => {
      if (!this.state.render) return render();
      return <ReqStatus inline {...this.state} />;
    };

    render() {
      return (
        <Component
          {...this.props}
          wrappedExecute={this.execute}
          reqStatus={this.state}
          renderIfLoaded={this.renderIfLoaded}
        />
      );
    }
  }

  const name = Component.displayName || Component.name || 'Component';
  WrappedComponent.displayName = `withReqStatus(${name})`;

  return WrappedComponent;
}
