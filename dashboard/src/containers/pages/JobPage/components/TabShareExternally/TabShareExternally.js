import React from 'react';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import classNames from 'classnames';

import formStyles from '@styles/form.module.scss';
import { StatusBar } from '@components';

import PrivateJobPosting from './components/PrivateJobPosting';
import CareerSiteJobPosting from './components/CareerSiteJobPosting';

import styles from './TabShareExternally.module.scss';

function TabShareExternally({ isAdmin, job, refreshJob }) {
  const isJobOpen = job.status === 'open';

  return (
    <div className={styles.root}>
      {!isJobOpen && (
        <div className={containerClassNames}>
          <StatusBar
            variant='warning'
            text={t`Your Job must be Open in order to share it externally`}
          />
        </div>
      )}
      <div className={containerClassNames}>
        <PrivateJobPosting
          refreshJob={refreshJob}
          job={job}
          canEnable={isAdmin && isJobOpen}
          isEditable={isAdmin}
        />
      </div>

      <div className={containerClassNames}>
        <CareerSiteJobPosting
          refreshJob={refreshJob}
          job={job}
          canEnable={isAdmin && isJobOpen}
          isEditable={isAdmin}
        />
      </div>
    </div>
  );
}

TabShareExternally.propTypes = {
  job: PropTypes.object.isRequired,
  refreshJob: PropTypes.func.isRequired,
  isAdmin: PropTypes.bool,
};

TabShareExternally.defaultProps = {
  isAdmin: false,
};

const containerClassNames = classNames(
  formStyles.formContainerWide,
  formStyles.bottomGap
);

export default TabShareExternally;
