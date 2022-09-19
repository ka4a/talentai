import React, { memo } from 'react';
import { useToggle } from 'react-use';
import { useSelector } from 'react-redux';
import {
  Collapse,
  Container,
  Nav,
  Navbar as BootstrapNavBar,
  NavbarToggler,
} from 'reactstrap';

import NotificationsDropdown from './components/NotificationDropdown';
import ShowAuthenticated from '../auth/ShowAuthenticated';
import HelpDropdown from './components/HelpDropdown';
import UserMenu from './components/UserMenu';
import Logo from '../UI/Logo';
import Menu from '../Menu';

import styles from './NavBar.module.scss';

const NavBar = () => {
  const [isOpen, toggle] = useToggle(false);

  const isLoaded = useSelector((state) => state.user.isLoaded);

  return (
    <BootstrapNavBar color='light' light expand='md' className={styles.container}>
      {isLoaded && <NavbarToggler onClick={toggle} />}

      {isLoaded && (
        <Collapse isOpen={isOpen} navbar className={styles.innerWrapper}>
          <Container>
            <div className={styles.navbarContainer}>
              <Logo variant='bodyStrong' />

              <Nav navbar>
                <Menu />
              </Nav>

              <div className={styles.navbarRight}>
                <ShowAuthenticated>
                  <HelpDropdown />
                  <NotificationsDropdown />
                  <UserMenu />
                </ShowAuthenticated>
              </div>
            </div>
          </Container>
        </Collapse>
      )}
    </BootstrapNavBar>
  );
};

export default memo(NavBar);
