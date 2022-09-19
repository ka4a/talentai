import React, { memo, useMemo } from 'react';
import { Button } from 'reactstrap';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { AGENCY_ADMINISTRATORS, AGENCY_MANAGERS } from '@constants';

import { ShowAuthenticated } from '../../auth';

const AGENCY_ADMINS_AND_MANAGERS = [AGENCY_ADMINISTRATORS, AGENCY_MANAGERS];

ApprovalButtons.propTypes = {
  form: PropTypes.object.isRequired,
  statusField: PropTypes.string,
  makeOnSubmit: PropTypes.func.isRequired,
};

ApprovalButtons.defaultProps = {
  statusField: 'status',
};

const useHandleClick = (makeOnSubmit, statusField, status) =>
  useMemo(
    () =>
      makeOnSubmit(
        { [statusField]: status },
        { isFinal: true, showToast: true, status }
      ),
    [makeOnSubmit, statusField, status]
  );

function ApprovalButtons(props) {
  const { makeOnSubmit, statusField, form } = props;

  const approve = useHandleClick(makeOnSubmit, statusField, 'approved');
  const sendToRevision = useHandleClick(makeOnSubmit, statusField, 'needs_revision');

  if (form[statusField] !== 'pending') return null;

  return (
    <ShowAuthenticated groups={AGENCY_ADMINS_AND_MANAGERS}>
      <Button onClick={sendToRevision} color='danger' className='ml-1'>
        <Trans>Send to revision</Trans>
      </Button>
      <Button onClick={approve} color='success' className='ml-1'>
        <Trans>Approve</Trans>
      </Button>
    </ShowAuthenticated>
  );
}

export default memo(ApprovalButtons);
