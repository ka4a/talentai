import React from 'react';

import classnames from 'classnames';
import PropTypes from 'prop-types';

export const Loading = ({ className }) => (
  <div className={classnames(className, 'mx-auto text-center')}>
    <span className='throbber-loader' />
  </div>
);

Loading.propTypes = {
  className: PropTypes.string,
};

Loading.defaultProps = {
  className: '',
};

export default Loading;
