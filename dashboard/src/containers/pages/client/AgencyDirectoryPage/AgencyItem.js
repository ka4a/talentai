import React, { memo, useCallback } from 'react';
import { Button } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import _ from 'lodash';
import { t, Trans } from '@lingui/macro';

import { delay, handleRequestError, openDialog } from '@utils';

import AgencyCategories from './AgencyCategories';
import AgencyLogo from './AgencyLogo';
import { CONTRACT_STATUS } from './constants';
import LocalPropTypes from './LocalPropTypes';
import AgencyContractDetails from './AgencyContractDetails';

import styles from './AgencyDirectory.module.scss';

export const getContactDetailsButtons = (resolve, reject) => (
  <>
    <Button onClick={resolve} variant='secondary' color='danger'>
      <Trans>End Contract</Trans>
    </Button>

    <Button onClick={reject}>
      <Trans>Close</Trans>
    </Button>
  </>
);

export const getConfirmEndContractButtons = (resolve, reject) => (
  <>
    <Button onClick={reject} variant='secondary'>
      <Trans>No</Trans>
    </Button>

    <Button onClick={resolve} variant='secondary' color='danger'>
      <Trans>Yes</Trans>
    </Button>
  </>
);

const DEFAULT_BUTTON_SETTINGS = {
  text: <Trans>Invite Agency</Trans>,
  color: 'primary',
};

const AGENCY_INVITED = {
  text: <Trans>Invited</Trans>,
  color: 'secondary',
  isDisabled: true,
};

const AGENCY_CONTRACT_BUTTON_SETTINGS = {
  [CONTRACT_STATUS.DEFAULT]: DEFAULT_BUTTON_SETTINGS,
  [CONTRACT_STATUS.PENDING]: AGENCY_INVITED,
  [CONTRACT_STATUS.AGENCY_INVITED]: AGENCY_INVITED,
  [CONTRACT_STATUS.EXPIRED]: AGENCY_INVITED,
  [CONTRACT_STATUS.INITIATED]: {
    text: <Trans>View Details</Trans>,
    color: 'nobg-primary',
  },
};

function AgencyItem(props) {
  const {
    agency,
    categoryGroups,
    categories,
    functionFocus,
    onInvite,
    onEndContract,
  } = props;

  const { name, nameJa, description, website, members } = agency;

  const buttonSettings =
    AGENCY_CONTRACT_BUTTON_SETTINGS[_.get(agency, 'contract.status')] ||
    DEFAULT_BUTTON_SETTINGS;

  const handleClickContract = useCallback(async () => {
    if (!agency.contract) {
      await onInvite(agency);
      return;
    }
    if (agency.contract.status === CONTRACT_STATUS.INITIATED) {
      try {
        await openDialog({
          title: t`Contract Details`,
          content: <AgencyContractDetails agency={agency} />,
          getButtons: getContactDetailsButtons,
        });

        await delay(300);

        await openDialog({
          title: t`End Contract`,
          description: t`Are you sure you want to end your contract with ${agency.name}`,
          getButtons: getConfirmEndContractButtons,
        });
        try {
          await onEndContract(agency);
        } catch (e) {
          handleRequestError(e, 'delete');
        }
      } catch (e) {
        // empty
      }
    }
  }, [agency, onInvite, onEndContract]);

  return (
    <div className='d-flex'>
      <div>
        <AgencyLogo agency={agency} />
      </div>
      <div className='ml-24 w-100'>
        <div className='d-flex'>
          <div>
            <div className='my-4'>
              <span
                className={classnames('font-weight-bold', {
                  'text-muted': !members.length,
                })}
              >
                {name}
              </span>
              {nameJa && <span className='text-muted'> ({nameJa})</span>}
            </div>

            {website && (
              <div>
                <a
                  href={website}
                  className='text-muted'
                  target='_blank'
                  rel='noopener noreferrer'
                >
                  {website}
                </a>
              </div>
            )}
          </div>

          <div className='ml-auto d-flex flex-column'>
            <div className='mt-auto'>
              <Button
                className={styles.button}
                disabled={buttonSettings.isDisabled}
                color={buttonSettings.color}
                onClick={handleClickContract}
              >
                {buttonSettings.text}
              </Button>
            </div>
          </div>
        </div>

        <div className='mt-16'>{description}</div>

        <div>
          {categoryGroups && functionFocus && (
            <AgencyCategories
              agency={agency}
              categoryGroups={categoryGroups}
              categories={categories}
              functionFocus={functionFocus}
            />
          )}
        </div>
      </div>
    </div>
  );
}

AgencyItem.propTypes = {
  agency: PropTypes.shape({
    name: PropTypes.string,
    nameJa: PropTypes.string,
    description: PropTypes.string,
    website: PropTypes.string,
    contract: PropTypes.shape({
      status: PropTypes.string,
    }),
    members: PropTypes.arrayOf(PropTypes.object),
  }),
  categoryGroups: LocalPropTypes.categoryGroups,
  categories: LocalPropTypes.arrayOfOptions,
  functionFocus: LocalPropTypes.arrayOfOptions,
  onInvite: PropTypes.func,
  onEndContract: PropTypes.func,
};

AgencyItem.defaultProps = {
  agency: {
    name: '',
    nameJa: '',
    description: '',
    website: '',
    contract: {
      status: CONTRACT_STATUS.DEFAULT,
    },
    members: [],
  },
  categoryGroups: [],
  categories: [],
  functionFocus: [],
  onInvite() {},
  onEndContract() {},
};

export default memo(AgencyItem);
