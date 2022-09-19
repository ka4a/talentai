import React from 'react';

import { Plural, t, Trans } from '@lingui/macro';

import { openDialog } from '@utils';
import { Button } from '@components';

export default function openCantBeFilled(availableOpenings) {
  return openDialog({
    title: t`Unfilled openings`,
    description: (
      <Trans>
        <Plural
          value={availableOpenings}
          one={`This job can't be marked as "Filled" as there is # open position.`}
          other={`This job can't be marked as "Filled" as there are # open positions.`}
        />
      </Trans>
    ),
    getButtons: (resolve) => (
      <Button onClick={resolve}>
        <Trans>Keep editing</Trans>
      </Button>
    ),
  });
}
