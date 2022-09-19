import React, { useEffect } from 'react';

import { withI18n } from '@lingui/react';
import { Trans } from '@lingui/macro';

import { showErrorToast } from '@utils';

function ErrorMessage() {
  return (
    <div className='d-flex flex-column'>
      <Trans>
        <div className='float-left'>
          <strong>Something went wrong.</strong>
        </div>
        <div>The development team has been notified and will look into the issue.</div>
      </Trans>
    </div>
  );
}

function ErrorWindow() {
  const showError = () => showErrorToast(<ErrorMessage />);

  useEffect(() => {
    window.addEventListener('error', showError);
    window.addEventListener('custom-error', showError);

    return () => window.removeEventListener('error', showError);
  }, []);

  return null;
}

export default withI18n()(ErrorWindow);
