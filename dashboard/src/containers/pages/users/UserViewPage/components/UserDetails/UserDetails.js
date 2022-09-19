import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { useStaffRead } from '@swrAPI';
import {
  PersonDetailsHeader,
  DetailsContainer,
  Badge,
  DetailsSection,
  DetailsContent,
  LabeledItem,
  DetailsGrid,
  ShowAuthenticated,
  Button,
} from '@components';
import { CLIENT_ADMINISTRATORS, LOCALE_CHOICES } from '@constants';
import { getChoiceName, getFormattedDate, mapChoiceNamesByValue } from '@utils';
import { useScrollToTop } from '@hooks';

import { useGroupToRoleMap } from '../../hooks';

import styles from './UserDetails.module.scss';

function UserDetails({ userId, basePath }) {
  const userSWR = useStaffRead(userId);
  const user = userSWR.data;
  const {
    firstName,
    lastName,
    photo,
    isActive,
    email,
    group,
    locale,
    country,
    dateJoined,
    lastLogin,
  } = user ?? {};
  const { loading, error } = userSWR;

  const { i18n } = useLingui();

  const groupToRoleMap = useGroupToRoleMap(i18n);
  const countryOptions = useSelector((state) => state.settings.localeData.countries);
  const countryNamesMap = useMemo(() => mapChoiceNamesByValue(countryOptions, 'code'), [
    countryOptions,
  ]);

  useScrollToTop();

  const renderDetails = () => (
    <>
      <PersonDetailsHeader
        title={`${firstName} ${lastName}`}
        avatarSrc={photo}
        controls={
          <ShowAuthenticated groups={[CLIENT_ADMINISTRATORS]}>
            <Button
              isLink
              to={`${basePath}/${userId}/edit`}
              color='primary'
              variant='secondary'
            >
              Edit
            </Button>
          </ShowAuthenticated>
        }
      >
        <span className={styles.badge}>
          {isActive ? (
            <Badge variant='normal' text={t`Active`} />
          ) : (
            <Badge variant='neutral' text={t`Inactive`} />
          )}
        </span>
        <div>{email}</div>
      </PersonDetailsHeader>
      <DetailsContent>
        <DetailsSection title={t`Details`}>
          <DetailsGrid columnCount={4}>
            <LabeledItem label={t`Role`} value={groupToRoleMap[group]} />
            <LabeledItem
              label={t`Language`}
              value={i18n._(getChoiceName(LOCALE_CHOICES, locale))}
            />
            <LabeledItem label={t`Country`} value={countryNamesMap[country]} />
          </DetailsGrid>
        </DetailsSection>
        <DetailsSection title={t`Metadata`}>
          <DetailsGrid columnCount={4}>
            <LabeledItem label={t`ID`} value={user.id} />
            <LabeledItem label={t`Last Login`} value={getFormattedDate(lastLogin)} />
            <LabeledItem label={t`Created Date`} value={getFormattedDate(dateJoined)} />
          </DetailsGrid>
        </DetailsSection>
      </DetailsContent>
    </>
  );

  return (
    <DetailsContainer
      data={user}
      isLoading={loading}
      error={error}
      renderDetails={renderDetails}
    />
  );
}

UserDetails.propTypes = {
  userId: PropTypes.number,
  basePath: PropTypes.string,
};

export default UserDetails;
