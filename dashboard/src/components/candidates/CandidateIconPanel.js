import React, { memo } from 'react';
import { MdArchive, MdContentCopy, MdGroup, MdAssignment } from 'react-icons/md';
import { TiInfoOutline } from 'react-icons/ti';
import { FaHandshake } from 'react-icons/fa';
import { AiFillTrophy, AiOutlineTrophy } from 'react-icons/ai';

import moment from 'moment-timezone';
import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import CandidateLabeledIcon from './CandidateLabeledIcon';

const renderPreviouslyPlaced = (isExpanded) => (
  <CandidateLabeledIcon
    key='placementPending'
    Icon={AiOutlineTrophy}
    isExpanded={isExpanded}
  >
    <Trans>Previously placed</Trans>
  </CandidateLabeledIcon>
);

const renderRecentlyPlaced = (isExpanded) => (
  <CandidateLabeledIcon
    key='placementPending'
    Icon={AiFillTrophy}
    isExpanded={isExpanded}
  >
    <Trans>Recently placed</Trans>
  </CandidateLabeledIcon>
);

const CandidateIconPanel = (props) => {
  const { candidate, proposal, isExpanded, className } = props;
  if (!candidate) return null;

  const {
    original,
    archived,
    isMet,
    isClientContact,
    isMissingRequiredFields,
    placementApprovedAt,
  } = candidate;

  const displayedIcons = [];

  if (isClientContact)
    displayedIcons.push(
      <CandidateLabeledIcon
        key='client_contact'
        Icon={FaHandshake}
        isExpanded={isExpanded}
      >
        <Trans>Candidate is currently a client contact</Trans>
      </CandidateLabeledIcon>
    );

  if (isMet)
    displayedIcons.push(
      <CandidateLabeledIcon key='met' Icon={MdGroup} isExpanded={isExpanded}>
        <Trans>Candidate has been met in person</Trans>
      </CandidateLabeledIcon>
    );

  if (archived)
    displayedIcons.push(
      <CandidateLabeledIcon key='archived' Icon={MdArchive} isExpanded={isExpanded}>
        <Trans>Archived</Trans>
      </CandidateLabeledIcon>
    );

  if (isMissingRequiredFields)
    displayedIcons.push(
      <CandidateLabeledIcon
        key='missing_info'
        Icon={TiInfoOutline}
        isExpanded={isExpanded}
      >
        <Trans>Missing information</Trans>
      </CandidateLabeledIcon>
    );

  if (original != null)
    displayedIcons.push(
      <CandidateLabeledIcon
        key='duplicate'
        Icon={MdContentCopy}
        isExpanded={isExpanded}
      >
        <Trans>Duplicate candidate?</Trans>
      </CandidateLabeledIcon>
    );

  if (proposal != null) {
    const { status, placementStatus, placementApprovedAt } = proposal;

    if (status.group === 'offer_accepted') {
      if (placementStatus === 'pending') {
        displayedIcons.push(
          <CandidateLabeledIcon
            key='placementPending'
            Icon={MdAssignment}
            isExpanded={isExpanded}
          >
            <Trans>Placement waiting approval</Trans>
          </CandidateLabeledIcon>
        );
      }
      if (placementStatus === 'approved' && placementApprovedAt) {
        displayedIcons.push(
          moment().diff(placementApprovedAt, 'months') > 6
            ? renderPreviouslyPlaced(isExpanded)
            : renderRecentlyPlaced(isExpanded)
        );
      }
    }
  } else if (placementApprovedAt) {
    displayedIcons.push(
      moment().diff(placementApprovedAt, 'months') > 6
        ? renderPreviouslyPlaced(isExpanded)
        : renderRecentlyPlaced(isExpanded)
    );
  }

  if (displayedIcons.length < 1) return null;

  return <div className={className}>{displayedIcons}</div>;
};

CandidateIconPanel.propTypes = {
  className: PropTypes.string,
  isExpanded: PropTypes.bool,
  candidate: PropTypes.shape({
    original: PropTypes.number,
    archived: PropTypes.bool,
    isClientContact: PropTypes.bool,
    isMet: PropTypes.bool,
    isMissingRequiredFields: PropTypes.bool,
  }),
  proposal: PropTypes.shape({
    feeId: PropTypes.number,
    placementStatus: PropTypes.number,
    status: PropTypes.shape({
      group: PropTypes.string,
    }),
  }),
};

CandidateIconPanel.defaultProps = {
  className: '',
  isExpanded: false,
  candidate: null,
};

export default memo(CandidateIconPanel);
