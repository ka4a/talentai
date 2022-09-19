import React, { useCallback, useContext, useState } from 'react';
import { FaUndoAlt } from 'react-icons/all';

import PropTypes from 'prop-types';
import classNames from 'classnames';
import { Trans } from '@lingui/macro';

import { Loading, Button } from '@components';
import formStyles from '@styles/form.module.scss';
import { FormContext } from '@contexts';
import fetcher from '@swrAPI/fetcher';
import { fetchErrorHandler } from '@utils';

import openResetJobPostingDialog from './openResetJobPostingDialog';
import { toJobPosting } from '../../utils';
import JobPostingFormContent from '../JobPostingFormContent';

import styles from './JobPostingForm.module.scss';

function JobPostingForm(props) {
  const { className } = props;

  const { form, setForm } = useContext(FormContext);
  const jobId = form.jobId;
  const [isResetting, setIsResetting] = useState(false);

  const handleReset = useCallback(async () => {
    try {
      await openResetJobPostingDialog();
    } catch (error) {
      return;
    }
    setIsResetting(true);
    try {
      const job = await fetcher(`/jobs/${jobId}`);
      setForm((form) => toJobPosting(job, form));
    } catch (error) {
      fetchErrorHandler(error);
    } finally {
      setIsResetting(false);
    }
  }, [setForm, jobId]);

  return (
    <div className={className}>
      <div className={formStyles.rowWrapper}>
        <div>
          <p className={formStyles.title}>
            <Trans>
              Edit your job posting content (may be different than your job details)
            </Trans>
          </p>
        </div>
      </div>
      <div className={classNames(styles.resetPanel, formStyles.title)}>
        <div>
          <Trans>Reset all changes to Job Details content</Trans>
        </div>
        <Button variant='secondary' color='neutral' onClick={handleReset}>
          <FaUndoAlt className={styles.resetIcon} />
          Reset Content
        </Button>
      </div>
      {isResetting ? <Loading className={styles.loading} /> : <JobPostingFormContent />}
    </div>
  );
}

JobPostingForm.propTypes = {
  className: PropTypes.string,
};

export default JobPostingForm;
