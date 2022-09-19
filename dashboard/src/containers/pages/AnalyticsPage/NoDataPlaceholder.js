import React from 'react';

import { Trans } from '@lingui/macro';

export default function NoDataPlaceholder() {
  return (
    <div className='w-100 h-100 d-flex justify-content-center align-items-center'>
      <div className='text-muted'>
        <Trans>No data.</Trans>
      </div>
    </div>
  );
}
