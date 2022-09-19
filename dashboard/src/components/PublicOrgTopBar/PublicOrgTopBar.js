import React from 'react';

import classNames from 'classnames';
import PropTypes from 'prop-types';

import LanguageMenu from '../LanguageMenu';

import styles from './PublicOrgTopBar.module.scss';

function PublicOrgTopBar({ title, logo }) {
  return (
    <div className={styles.root}>
      <div className={classNames(styles.content, 'container')}>
        <div className={styles.side}>
          {logo && <img src={logo} alt={title} className={styles.logo} />}
        </div>
        <h3 className={classNames(styles.title, { [styles.noLogo]: !logo })}>
          {title}
        </h3>

        <div className={styles.side}>
          <div className={styles.poweredBy}>
            Powered by <a href='https://zookeep.com'>ZooKeep</a>
          </div>
        </div>

        <LanguageMenu />
      </div>
    </div>
  );
}

PublicOrgTopBar.propTypes = {
  title: PropTypes.string,
  logo: PropTypes.string,
};

PublicOrgTopBar.defaultProps = {
  title: '',
  logo: null,
};

export default PublicOrgTopBar;
