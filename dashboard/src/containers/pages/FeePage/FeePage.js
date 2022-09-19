import React, { memo, useState, useCallback } from 'react';

import PropTypes from 'prop-types';
import { compose } from 'redux';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { fetchErrorHandler } from '@utils';
import { client } from '@client';

import BaseFeePage from './BaseFeePage';

FeePage.propTypes = {
  i18n: PropTypes.shape({
    _: PropTypes.func.isRequired,
  }).isRequired,
  match: PropTypes.shape({
    params: PropTypes.shape({
      feeId: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
};

const wrapper = compose(memo, withI18n());

function FeePage(props) {
  const { i18n, match } = props;
  const { feeId } = match.params;

  const [proposal, setProposal] = useState(null);

  const handleFetch = useCallback(
    async (form) => {
      if (form.proposal) {
        try {
          const { obj } = await client.execute({
            operationId: 'proposals_read',
            parameters: {
              id: form.proposal,
              extra_fields: 'hired_at,job_created_by_name',
            },
          });
          setProposal(obj);
        } catch (error) {
          fetchErrorHandler(error);
        }
      }
    },
    [setProposal]
  );

  let title = proposal
    ? i18n._(t`${proposal.candidate.name} placement form`)
    : i18n._(t`Placement form`);

  return (
    <BaseFeePage
      title={title}
      proposal={proposal}
      feeId={feeId}
      onFetch={handleFetch}
    />
  );
}

export default wrapper(FeePage);
