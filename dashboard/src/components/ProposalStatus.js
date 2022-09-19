import React from 'react';

import classnames from 'classnames';

const GROUP_COLORS = {
  // shortlist
  new: 'dark',
  approved: 'warning',
  rejected: 'muted',
  interviewing: 'warning',
  proceeding: 'warning',
  offer: 'warning',
  offer_accepted: 'success',
  offer_declined: 'muted',
  candidate_quit: 'muted',
  closed: 'muted',
  // longlist
  not_contacted: 'muted',
  interested: 'dark',
  not_interested: 'dark',
  interviewed_internally: 'dark',
  pending_feedback: 'dark',
  early_rejected: 'muted',
};

export default function ProposalStatus({ status }) {
  const color = GROUP_COLORS[status.group];

  return (
    <span className={classnames({ [`text-${color}`]: color })}>{status.status}</span>
  );
}
