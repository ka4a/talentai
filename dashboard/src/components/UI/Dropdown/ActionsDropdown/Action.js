import React, { useCallback } from 'react';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import Typography from '@components/UI/Typography';

import styles from './ActionsDropdown.module.scss';

function Action(props) {
  const { toggleDropdown, handler, transKey, text, link } = props;

  const handleClick = useCallback(
    (event) => {
      event.stopPropagation();
      if (handler) handler();
      toggleDropdown();
    },
    [handler, toggleDropdown]
  );

  const textContent = (
    <Typography variant='caption'>
      {text != null ? text : <Trans id={transKey} />}
    </Typography>
  );

  if (link)
    return (
      <a className={styles.option} href={link}>
        {textContent}
      </a>
    );

  return (
    <div className={styles.option} onClick={handleClick}>
      {textContent}
    </div>
  );
}

Action.propTypes = {
  toggleDropdown: PropTypes.func.isRequired,
  handler: PropTypes.func,
  transKey: PropTypes.string,
  text: PropTypes.string,
  link: PropTypes.string,
};

export default Action;
