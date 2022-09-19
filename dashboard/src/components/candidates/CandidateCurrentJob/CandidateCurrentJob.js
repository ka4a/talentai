import React, { memo, useMemo } from 'react';
import { UncontrolledTooltip } from 'reactstrap';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { Typography } from '@components';

import styles from './CandidateCurrentJob.module.scss';

const CandidateCurrentJob = ({ className, candidate, withTooltip }) => {
  const { currentPosition, currentCompany, id } = candidate;

  const jobTitle = useMemo(
    () =>
      `${currentPosition}${
        currentPosition && currentCompany && ` at `
      }${currentCompany}`,
    [currentCompany, currentPosition]
  );

  return (
    <>
      <div id={`candidateCurrentJobTooltip${id}`} className={className}>
        <Typography variant='caption' className={styles.text}>
          <span className={styles.position}>{currentPosition}</span>

          {currentPosition && currentCompany && (
            <span className={styles.company}>
              <Trans>{`at ${currentCompany}`}</Trans>
            </span>
          )}

          <span className={styles.company}>{!currentPosition && currentCompany}</span>
        </Typography>
      </div>

      {jobTitle && withTooltip && (
        <UncontrolledTooltip target={`candidateCurrentJobTooltip${id}`}>
          <span>{jobTitle}</span>
        </UncontrolledTooltip>
      )}
    </>
  );
};

CandidateCurrentJob.propTypes = {
  className: PropTypes.string,
  candidate: PropTypes.shape({
    id: PropTypes.number,
    currentPosition: PropTypes.string,
    currentCompany: PropTypes.string,
  }),
  withTooltip: PropTypes.bool,
};

CandidateCurrentJob.defaultProps = {
  className: '',
  candidate: {},
  withTooltip: false,
};

export default memo(CandidateCurrentJob);
