import React, { memo, useCallback, useMemo, useState } from 'react';
import { Dropdown, DropdownToggle, DropdownMenu } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import {
  checkIfPastInterviewTime,
  fetchErrorHandler,
  isDialogCanceled,
  formatStageLabel,
} from '@utils';
import { useGetJob, useProposalsList, useProposalsRead } from '@swrAPI';
import { INTERVIEW_STATUSES, PROPOSAL_STAGES } from '@constants';
import { client } from '@client';

import openMoveToInterviewing from './dialogs/openMoveToInterviewing';
import Typography from '../../Typography';

import styles from './StagesDropdown.module.scss';

const StagesDropdown = ({ title, options }) => {
  const { mutate: refreshJob } = useGetJob();
  const { mutate: refreshStages } = useProposalsList();
  const { data, mutate: refreshProposal } = useProposalsRead();
  const { id, job = {}, stage, status = {}, isRejected, interviews = [] } = data;

  const [dropdownOpen, setDropdownOpen] = useState(false);

  const toggle = () => setDropdownOpen((prevState) => !prevState);
  const sendRequest = useCallback(
    async (value) => {
      try {
        await client.execute({
          operationId: 'proposals_partial_update',
          parameters: { id, data: { status: value } },
        });

        await Promise.all([refreshJob(), refreshProposal(), refreshStages()]);
      } catch (error) {
        fetchErrorHandler(error);
      }
    },
    [id, refreshJob, refreshProposal, refreshStages]
  );

  const onChange = useCallback(
    async (value) => {
      toggle();
      await sendRequest(value);
    },
    [sendRequest]
  );

  const isInterviewingStage = stage === PROPOSAL_STAGES.interviewing;
  const areInterviewsCompleted = useMemo(
    () =>
      interviews.every((interview) => {
        const { status, assessment, endAt } = interview;
        const hasAssessment = status === INTERVIEW_STATUSES.scheduled && assessment;
        const isSkipped = status === INTERVIEW_STATUSES.skipped;
        return hasAssessment || isSkipped || checkIfPastInterviewTime(endAt);
      }),
    [interviews]
  );

  const onClickInterviewing = useCallback(async () => {
    if (isInterviewingStage || areInterviewsCompleted || isRejected) return;

    if (await isDialogCanceled(openMoveToInterviewing())) return false;

    const interviewingId = options[0].value;
    await sendRequest(interviewingId);
  }, [areInterviewsCompleted, isInterviewingStage, isRejected, options, sendRequest]);

  const isActive = stage === title;

  if (title === PROPOSAL_STAGES.interviewing) {
    return (
      <div
        onClick={onClickInterviewing}
        className={classnames(styles.title, {
          [styles.active]: isActive,
          [styles.disabled]: areInterviewsCompleted || isRejected,
        })}
      >
        {title}
      </div>
    );
  }

  return (
    <Dropdown isOpen={dropdownOpen} toggle={toggle} disabled={isRejected}>
      <DropdownToggle
        disabled={isInterviewingStage}
        className={classnames(styles.title, {
          [styles.active]: isActive,
          [styles[title]]: title,
          [styles.disabled]: isRejected || isInterviewingStage,
        })}
      >
        {title}
      </DropdownToggle>

      <DropdownMenu className={styles.menu}>
        {options.map((option) => (
          <Typography
            key={option.value}
            variant='caption'
            className={classnames(styles.option, {
              [styles.active]: option.group === status.group,
            })}
            onClick={() => onChange(option.value)}
          >
            {formatStageLabel(option.label, job?.orgType)}
          </Typography>
        ))}
      </DropdownMenu>
    </Dropdown>
  );
};

StagesDropdown.propTypes = {
  title: PropTypes.string,
  options: PropTypes.array,
};

StagesDropdown.defaultProps = {
  title: '',
  options: [],
};
export default memo(StagesDropdown);
