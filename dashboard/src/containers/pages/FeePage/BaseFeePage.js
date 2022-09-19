import React, { memo } from 'react';

import PropTypes from 'prop-types';

import { DefaultPageContainer } from '@components';

import FeeForm from '../../../components/fee/FeeForm';

BaseFeePage.propTypes = {
  feeId: PropTypes.number,
  proposal: PropTypes.object,
  match: PropTypes.shape({
    params: PropTypes.shape({
      proposalId: PropTypes.string.isRequired,
      feeId: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
  onFetch: PropTypes.func,
};

function BaseFeePage(props) {
  const { feeId, proposal, title, onFetch } = props;

  return (
    <DefaultPageContainer
      title={title}
      colAttrs={{ xs: 12, md: { size: 8, offset: 2 } }}
    >
      <FeeForm onFetch={onFetch} title={title} proposal={proposal} feeId={feeId} />
    </DefaultPageContainer>
  );
}

export default memo(BaseFeePage);
