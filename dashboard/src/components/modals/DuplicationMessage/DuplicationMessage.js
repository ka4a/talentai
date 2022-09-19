import React, { memo, useMemo } from 'react';

import moment from 'moment';
import PropTypes from 'prop-types';
import { Trans, Plural } from '@lingui/macro';

import LocalPropTypes from './localPropTypes';
import Notice from './Notice';

import noticeStyles from './Notice.module.scss';

const SUBMITTED_BY_OTHER = {
  POSSIBLE: (
    <Trans>
      This candidate might have been submitted for this job by another organization.
    </Trans>
  ),
  ABSOLUTE: (
    <Trans>
      This candidate has already been submitted for this job by another organization.
    </Trans>
  ),
};

const DEFINITELY_SUBMITTED = {
  [true]: <Trans>You have already submitted this candidate to this job</Trans>,
  [false]: <Trans>You may have already submitted this candidate to this job</Trans>,
};

const IN_DB = {
  [true]: <Trans>This candidate is already in your db</Trans>,
  [false]: <Trans>This candidate might be already in your db</Trans>,
};

function daysSince(date) {
  return moment().diff(moment(date), 'days');
}

function DuplicationMessage(props) {
  const { lastSubmitted, duplicates, submittedByOthers } = props;

  const daysSinceLastSubmitted = daysSince(lastSubmitted);

  const submittedBySelf = useMemo(() => {
    return duplicates.filter((e) => e.isSubmitted);
  }, [duplicates]);

  const inDb = useMemo(() => {
    return duplicates.filter((e) => !e.isSubmitted);
  }, [duplicates]);

  const definitelySubmitted = useMemo(() => {
    return duplicates.some((e) => e.isSubmitted && e.isAbsolute);
  }, [duplicates]);

  const definitelyInDB = useMemo(() => {
    return duplicates.some((e) => e.isAbsolute);
  }, [duplicates]);

  return (
    <div>
      {submittedByOthers !== null && (
        <div className={noticeStyles.title}>
          {SUBMITTED_BY_OTHER[submittedByOthers]}
        </div>
      )}
      <Notice list={submittedBySelf}>
        {DEFINITELY_SUBMITTED[definitelySubmitted]}
        <span>&nbsp;</span>
        <Plural
          value={daysSinceLastSubmitted}
          _0='today'
          _1='yesterday'
          other='# days ago'
        />
      </Notice>
      <Notice list={inDb} fieldName='inDb' showCandidates>
        {IN_DB[definitelyInDB]}
      </Notice>

      <Trans>Do you want to proceed anyway?</Trans>
    </div>
  );
}

DuplicationMessage.propTypes = {
  duplicates: PropTypes.arrayOf(LocalPropTypes.candidate),
  submittedByOthers: PropTypes.oneOf(Object.values(SUBMITTED_BY_OTHER)),
  lastSubmitted: PropTypes.string,
};
DuplicationMessage.defaultProps = {
  duplicates: [],
  submittedByOthers: null,
  lastSubmitted: null,
};

export default memo(DuplicationMessage);
