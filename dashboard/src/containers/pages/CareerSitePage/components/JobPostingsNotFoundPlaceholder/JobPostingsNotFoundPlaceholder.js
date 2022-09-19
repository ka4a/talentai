import React from 'react';

import { t, Trans } from '@lingui/macro';

import { TablePlaceholder, Typography } from '@components';
import searchIcon from '@images/icons/no-results-found.svg';

function NoJobPostingsPlaceholder() {
  return (
    <TablePlaceholder
      title={t`No Openings found`}
      icon={<img src={searchIcon} width={213} height={186} alt='search' />}
    >
      <Trans>
        <Typography>You can try to adjust your search or filters</Typography>
      </Trans>
    </TablePlaceholder>
  );
}

export default NoJobPostingsPlaceholder;
