import React from 'react';

import { Trans } from '@lingui/macro';

export default function ErrorPlaceholder() {
  return (
    <div className='w-100 h-100 d-flex justify-content-center align-items-center'>
      <div className='text-muted'>
        <Trans>An error occurred.</Trans>
      </div>
    </div>
  );
}
