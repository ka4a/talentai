import React, { Component } from 'react';

import PropTypes from 'prop-types';
import classNames from 'classnames';

import SimpleTooltip from './SimpleTooltip';
import Typography from '../UI/Typography';

const CandidateLabeledIcon = (props) => {
  const { isExpanded, iconClassName, children, Icon } = props;

  if (isExpanded)
    return (
      <div>
        <Icon className={iconClassName} />{' '}
        <Typography>
          <>
            {' - '}
            {children}
          </>
        </Typography>
      </div>
    );

  return (
    <SimpleTooltip content={children}>
      <Icon className={classNames('mr-1', iconClassName)} />
    </SimpleTooltip>
  );
};

CandidateLabeledIcon.propTypes = {
  Icon: PropTypes.oneOfType([PropTypes.func, PropTypes.instanceOf(Component)])
    .isRequired,
  isExpanded: PropTypes.bool,
  iconClassName: PropTypes.string,
};

CandidateLabeledIcon.defaultProps = {
  isExpanded: false,
  iconClassName: '',
};

export default CandidateLabeledIcon;
