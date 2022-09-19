import React, { useCallback } from 'react';

import { Trans } from '@lingui/macro';

import { FormSectionOld } from '../../FormSectionOld';

export function useFormTop(proposal) {
  const job = proposal ? proposal.job : {};
  const { clientName, title } = job || {};

  return useCallback(
    (form) => (
      <FormSectionOld>
        {clientName && title ? (
          <div>
            {clientName} - {title}
          </div>
        ) : null}
        {form.submittedBy ? (
          <h4 className='text-muted font-weight-normal mt-2'>
            <Trans>
              Submitted by {form.submittedBy.firstName} {form.submittedBy.lastName}
            </Trans>
          </h4>
        ) : null}
      </FormSectionOld>
    ),
    [clientName, title]
  );
}
