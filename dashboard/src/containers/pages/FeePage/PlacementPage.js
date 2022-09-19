import React, { memo, useMemo } from 'react';

import PropTypes from 'prop-types';
import { compose } from 'redux';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import ReqStatus from '@components/ReqStatus';
import { useSwagger } from '@hooks';

import BaseFeePage from './BaseFeePage';

PlacementPage.propTypes = {
  i18n: PropTypes.shape({
    _: PropTypes.func.isRequired,
  }).isRequired,
  match: PropTypes.shape({
    params: PropTypes.shape({
      proposalId: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

function useProposalSwagger(proposalId) {
  const parameters = useMemo(
    () => ({
      id: proposalId,
      extra_fields: 'hired_at,job_created_by_name,placement_id',
    }),
    [proposalId]
  );
  return useSwagger('proposals_read', parameters);
}

const wrapper = compose(memo, withI18n());

function PlacementPage(props) {
  const { i18n } = props;

  const proposalId = props.match.params.proposalId;

  const proposalSwagger = useProposalSwagger(proposalId);
  const proposal = proposalSwagger.obj;

  const loading = proposalSwagger.loading;

  const error = proposalSwagger.error;

  if (!proposal || error) return <ReqStatus loading={loading} error={error} />;

  return (
    <BaseFeePage
      title={i18n._(t`${proposal.candidate.name} placement form`)}
      feeId={proposal.feeId}
      proposal={proposal}
    />
  );
}

export default wrapper(PlacementPage);
