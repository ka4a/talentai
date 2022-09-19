import React, { memo, useCallback } from 'react';
import { Button, Badge } from 'reactstrap';
import { connect } from 'react-redux';

import _ from 'lodash';
import PropTypes from 'prop-types';
import classnames from 'classnames';
import { Trans } from '@lingui/macro';

import { handleRequestError } from '@utils';
import { AGENCY_GROUPS } from '@constants';

import { CONTRACT_STATUS } from '../client/AgencyDirectoryPage/constants';
import Job from './Job';
import { client as api } from '../../../client';

import styles from './Invitation.module.scss';

const reduxConnector = connect((state) => ({
  isAgency: _.intersection(state.user.groups, AGENCY_GROUPS).length > 0,
}));

const EXPIREABLE_STATUSES = [CONTRACT_STATUS.AGENCY_INVITED, CONTRACT_STATUS.PENDING];

const canExpire = (status) => _.includes(EXPIREABLE_STATUSES, status);

function Invitation(props) {
  const {
    id,
    jobs,
    client,
    agency,
    status,
    isAgency,
    isAgencySigned,
    isClientSigned,
    updateInvite,
    daysUntilInvitationExpire,
  } = props;
  const isExpired =
    (daysUntilInvitationExpire <= 0 && canExpire(status)) ||
    status === CONTRACT_STATUS.EXPIRED;

  const invitationName = isAgency ? client.name : agency.name;

  const update = useCallback(
    async (data) => {
      try {
        await api.execute({
          parameters: { id, data },
          operationId: 'contracts_partial_update',
        });
        updateInvite();
      } catch (e) {
        handleRequestError(e, 'patch');
      }
    },
    [id, updateInvite]
  );

  const isSigned = isAgency ? isAgencySigned : isClientSigned;

  const sign = useCallback(
    () => update(isAgency ? { isAgencySigned: true } : { isClientSigned: true }),
    [isAgency, update]
  );

  const acceptInvite = useCallback(() => update({ status: CONTRACT_STATUS.PENDING }), [
    update,
  ]);
  const rejectInvite = useCallback(() => update({ status: CONTRACT_STATUS.REJECTED }), [
    update,
  ]);

  return (
    <div>
      {isAgency && !isExpired && status === CONTRACT_STATUS.AGENCY_INVITED ? (
        <>
          <h4 className='text-dark'>
            <Trans>Client {client.name} has invited you to see their jobs.</Trans>
          </h4>
          <div>
            <Trans>Invitation will expire in {daysUntilInvitationExpire} days</Trans>
          </div>
          <div className={styles.actions}>
            <Button onClick={acceptInvite} className={styles.action} color='primary'>
              <Trans>Accept</Trans>
            </Button>
            <Button onClick={rejectInvite} className={styles.action} color='danger'>
              <Trans>Decline</Trans>
            </Button>
          </div>
        </>
      ) : (
        <>
          <h4 className='text-dark'>
            <Trans>{invitationName} invitation</Trans>
          </h4>
          <div className='d-flex'>
            {status === CONTRACT_STATUS.REJECTED && (
              <Badge color='danger'>
                <Trans>Rejected</Trans>
              </Badge>
            )}
            {isExpired && (
              <Badge color='danger'>
                <Trans>Expired</Trans>
              </Badge>
            )}
            {!isAgency && status === CONTRACT_STATUS.PENDING && (
              <div className={styles.expires}>
                <Trans>Agency can see your jobs.</Trans>
              </div>
            )}
            {!isExpired && canExpire(status) && (
              <div className={styles.expires}>
                <Trans>Expires in {daysUntilInvitationExpire} days</Trans>
              </div>
            )}
          </div>

          {isAgency && jobs && jobs.length > 0 && (
            <div className={styles.jobContainer}>
              <div className={classnames('text-dark', styles.jobListTitle)}>
                <Trans>Jobs:</Trans>
              </div>
              <div>
                {jobs.map((job) => (
                  <Job key={job.id} {...job} />
                ))}
              </div>
            </div>
          )}

          {status === CONTRACT_STATUS.PENDING &&
            (isSigned ? (
              <div className={classnames('text-dark', styles.signatureConfirmed)}>
                <Trans>Signature Confirmed</Trans>
              </div>
            ) : (
              <div className={styles.actions}>
                <Button onClick={sign} color={'primary'} className={styles.action}>
                  <Trans>Confirm Contract</Trans>
                </Button>
              </div>
            ))}
        </>
      )}
    </div>
  );
}

const LocalPropTypes = {
  organisation: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
  }),
};

Invitation.propTypes = {
  isAgency: PropTypes.bool.isRequired,
  id: PropTypes.number.isRequired,
  status: PropTypes.oneOf(Object.values(CONTRACT_STATUS)).isRequired,
  updateInvite: PropTypes.func.isRequired,
  daysUntilInvitationExpire: PropTypes.number.isRequired,
  client: LocalPropTypes.organisation.isRequired,
  agency: LocalPropTypes.organisation.isRequired,
  isClientSigned: PropTypes.bool.isRequired,
  isAgencySigned: PropTypes.bool.isRequired,
  jobs: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      title: PropTypes.string,
    })
  ),
};

export default reduxConnector(memo(Invitation));
