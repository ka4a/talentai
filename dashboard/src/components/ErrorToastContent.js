import React from 'react';

import PropTypes from 'prop-types';
import { Trans, defineMessage } from '@lingui/macro';

function ErrorToastContent({ title, message }) {
  return (
    <div className='d-flex flex-column'>
      <div className='float-left'>
        <strong>
          <Trans id={title} />
        </strong>
      </div>
      <div>
        <Trans id={message} />
      </div>
    </div>
  );
}

ErrorToastContent.propTypes = {
  title: PropTypes.string,
  message: PropTypes.string,
};

ErrorToastContent.defaultProps = {
  title: defineMessage({ message: 'Something went wrong.' }).id,
  message: defineMessage({
    message: 'The development team has been notified and will look into the issue.',
  }).id,
};

export default ErrorToastContent;
