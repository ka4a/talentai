import React, { memo } from 'react';
import { Link } from 'react-scroll';

import { Trans } from '@lingui/macro';
import PropTypes from 'prop-types';

import Typography from '../Typography';
import WindowBackground from '../WindowBackground';

import styles from './SectionsMenu.module.scss';

const SectionsMenu = ({ sections }) => (
  <WindowBackground className={styles.menu}>
    {sections.map((item) => (
      <Typography key={item.id} variant='caption'>
        <Link
          activeClass={styles.isActive}
          className={styles.menuItem}
          duration={500}
          to={item.id}
          offset={-20}
          smooth
          spy
        >
          <Trans id={item.label} />
        </Link>
      </Typography>
    ))}
  </WindowBackground>
);

SectionsMenu.propTypes = {
  sections: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      label: PropTypes.string,
    })
  ).isRequired,
};

export default memo(SectionsMenu);
