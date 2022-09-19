import React from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import styles from './Job.module.scss';

// would be easier to turn it into link or alter it if it's component
function Job(props) {
  const { title, responsibilities } = props;
  return (
    <div className={classnames(styles.container, 'border-light')}>
      <h4 className={classnames('text-dark', styles.title)}>{title}</h4>
      <div
        className={classnames('text-dark', styles.responsibilities)}
        dangerouslySetInnerHTML={{ __html: responsibilities }}
      />
    </div>
  );
}

Job.propTypes = {
  title: PropTypes.string,
  responsibilities: PropTypes.string,
};
Job.defaultProps = {
  title: '',
  responsibilities: '',
};

export default Job;
