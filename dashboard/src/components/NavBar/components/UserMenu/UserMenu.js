import React, { useCallback } from 'react';
import { FiLogOut, HiOutlineBriefcase, HiOutlineCog } from 'react-icons/all';
import { useDispatch, useSelector } from 'react-redux';
import { Link, useHistory } from 'react-router-dom';
import { DropdownItem } from 'reactstrap';

import { t, Trans } from '@lingui/macro';

import ShowAuthenticated from '@components/auth/ShowAuthenticated';
import SimpleDropdown from '@components/SimpleDropdown';
import { CLIENT_ADMINISTRATORS } from '@constants';
import { useLegalAgreementsList } from '@swrAPI';
import Avatar from '@components/UI/Avatar';
import { logoutUser } from '@actions';
import { useCareerSiteUrl } from '@hooks';

import UserMenuItem from './components/UserMenuItem';

import styles from './UserMenu.module.scss';

const UserMenu = () => {
  const { privacyPolicyLink, termsAndConditionsLink } = useLegalAgreementsList();
  const history = useHistory();

  const user = useSelector((state) => state.user);

  const careerSiteUrl = useCareerSiteUrl();
  const isCareerSiteEnabled = user?.profile.org.isCareerSiteEnabled;

  const dispatch = useDispatch();

  const logout = useCallback(async () => {
    await dispatch(logoutUser());
    history.push('/login');
  }, [dispatch, history]);

  const renderLink = (text, link) => (
    <DropdownItem tag='a' href={link} className={styles.footerLink} target='_blank'>
      {text}
    </DropdownItem>
  );

  const renderSettingsLink = (link, text) => (
    <UserMenuItem tag={Link} to={link}>
      <HiOutlineCog className={styles.cog} />
      {text}
    </UserMenuItem>
  );

  return (
    <>
      <SimpleDropdown
        menuClassname={styles.wrapper}
        buttonClassname={styles.trigger}
        trigger={<Avatar src={user.photo} size='xs' />}
      >
        <div className={styles.infoWrapper}>
          <div className={styles.avatar}>
            <Avatar src={user.photo} />
          </div>

          <div>
            <div className={styles.name}>
              {user.firstName} {user.lastName}
            </div>

            <div className={styles.org}>{user.profile?.org?.name}</div>
          </div>
        </div>

        {renderSettingsLink('/settings/personal', t`Personal Settings`)}

        <ShowAuthenticated groups={CLIENT_ADMINISTRATORS_GROUP}>
          {renderSettingsLink('/settings/company', t`Company Settings`)}
          {isCareerSiteEnabled && (
            <UserMenuItem tag='a' href={careerSiteUrl}>
              <HiOutlineBriefcase className={styles.briefcase} />
              <Trans>Career Site</Trans>
            </UserMenuItem>
          )}
        </ShowAuthenticated>

        <UserMenuItem onClick={logout}>
          <FiLogOut className={styles.logout} />
          <Trans>Logout</Trans>
        </UserMenuItem>

        <div className={styles.footer}>
          {renderLink(t`Privacy Policy`, privacyPolicyLink)}
          <span>•</span>
          {renderLink(t`Terms & Conditions`, termsAndConditionsLink)}
        </div>
      </SimpleDropdown>
    </>
  );
};

const CLIENT_ADMINISTRATORS_GROUP = [CLIENT_ADMINISTRATORS];

export default UserMenu;
