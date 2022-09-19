import React, { memo } from 'react';
import { UncontrolledTooltip } from 'reactstrap';

import PropTypes from 'prop-types';

const JobTitle = (props) => {
  const { className, linkClassName, job, link, withTooltip } = props;
  const { title, id } = job;

  const showTooltip = title && withTooltip;

  return (
    <span className={className}>
      <div id={`jobTitleTooltip${id}`}>
        {link ? (
          <div className={linkClassName}>
            {title.length > 90 ? `${title.substr(0, 90)}...` : title}
          </div>
        ) : (
          <span>{title}</span>
        )}
      </div>

      {showTooltip && (
        <UncontrolledTooltip target={`jobTitleTooltip${id}`}>
          <span className='text-capitalize'>{title}</span>
        </UncontrolledTooltip>
      )}
    </span>
  );
};

JobTitle.propTypes = {
  className: PropTypes.string,
  linkClassName: PropTypes.string,
  link: PropTypes.bool,
  withTooltip: PropTypes.bool,
};

JobTitle.defaultProps = {
  className: '',
  linkClassName: '',
  link: false,
  withTooltip: false,
};

export default memo(JobTitle);
