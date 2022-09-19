import React from 'react';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { TablePlaceholder, Typography } from '@components';
import searchIcon from '@images/icons/no-results-found.svg';

function NotFoundTablePlaceholder({ title }) {
  return (
    <TablePlaceholder
      title={title}
      icon={<img src={searchIcon} width={213} height={186} alt='search' />}
    >
      <Typography>
        <Trans>You can try to adjust your search or filters</Trans>
      </Typography>
    </TablePlaceholder>
  );
}

NotFoundTablePlaceholder.propTypes = {
  title: PropTypes.string.isRequired,
};

export default NotFoundTablePlaceholder;
