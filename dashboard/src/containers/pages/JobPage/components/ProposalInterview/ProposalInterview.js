import React, { memo } from 'react';
import { useToggle } from 'react-use';
import { Collapse as CollapseRS } from 'reactstrap';

import classnames from 'classnames';
import PropTypes from 'prop-types';
import { useLingui } from '@lingui/react';

import { Typography } from '@components';
import { INTERVIEW_TYPES_CHOICES } from '@constants';
import { getChoiceName } from '@utils';
import { useTranslatedChoices } from '@hooks';

import InterviewFullBody from './components/InterviewFullBody';
import HeaderActionsFull from './components/HeaderActionsFull';
import InterviewShortBody from './components/InterviewShortBody';
import HeaderActionsShort from './components/HeaderActionsShort';

import styles from './ProposalInterview.module.scss';

const ProposalInterview = ({ interview, shortMode }) => {
  const {
    order,
    interviewer,
    description,
    isCurrentInterview,
    interviewType: sourceType,
  } = interview;

  const { i18n } = useLingui();
  const interviewTypesChoices = useTranslatedChoices(i18n, INTERVIEW_TYPES_CHOICES);
  const [isOpen, toggle] = useToggle(isCurrentInterview);

  const interviewerName = interviewer
    ? `${interviewer.firstName} ${interviewer.lastName}`
    : '';

  const isDisabled = Boolean(shortMode && !description);
  const isCollapseOpen = isDisabled ? false : isOpen;

  const HeaderActions = shortMode ? HeaderActionsShort : HeaderActionsFull;
  const Body = shortMode ? InterviewShortBody : InterviewFullBody;

  return (
    <div className={styles.item}>
      <div
        className={classnames(styles.header, {
          [styles.isOpen]: isCollapseOpen,
          [styles.disabled]: isDisabled,
        })}
        onClick={isDisabled ? null : toggle}
      >
        <div className={styles.title}>
          <Typography variant='button' className={styles.count}>
            {order}
          </Typography>

          <Typography>
            {getChoiceName(interviewTypesChoices, sourceType) ?? ''}
          </Typography>
        </div>

        <HeaderActions
          interview={interview}
          isDisabled={isDisabled}
          isOpen={isCollapseOpen}
          interviewerName={interviewerName}
        />
      </div>

      <CollapseRS isOpen={isCollapseOpen}>
        <Body interview={interview} interviewerName={interviewerName} />
      </CollapseRS>
    </div>
  );
};

ProposalInterview.propTypes = {
  interview: PropTypes.shape({
    interviewer: PropTypes.object,
    description: PropTypes.string,
    isCurrentInterview: PropTypes.bool,
  }).isRequired,
  shortMode: PropTypes.bool,
};

ProposalInterview.defaultProps = {
  shortMode: false,
};

export default memo(ProposalInterview);
