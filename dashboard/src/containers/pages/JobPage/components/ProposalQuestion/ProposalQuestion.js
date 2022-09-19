import React, { useState, memo, useCallback } from 'react';
import { useToggle } from 'react-use';
import { Collapse as CollapseRS } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';

import { client } from '@client';
import { useProposalsRead } from '@swrAPI';
import { fetchErrorHandler } from '@utils';
import { LabeledItem, LabeledRichEditor, Typography } from '@components';

import ProposalQuestionButtons from './components/QuestionButtons';
import QuestionHeaderButtons from './components/QuestionHeaderButtons';

import styles from './ProposalQuestion.module.scss';

const ProposalQuestion = ({ index, question }) => {
  const { id, text, answer } = question;

  const [isOpen, toggle] = useToggle(false);

  const [isEditMode, setIsEditMode] = useState(false);
  const [editingValue, setEditingValue] = useState('');

  const { mutate: refreshProposal } = useProposalsRead();

  const activateEditMode = useCallback(() => {
    setEditingValue(answer);
    setIsEditMode(true);
    if (!isOpen) toggle();
  }, [answer, isOpen, toggle]);

  const disableEditMode = useCallback(() => {
    setEditingValue('');
    setIsEditMode(false);
  }, []);

  const saveAnswer = useCallback(async () => {
    try {
      await client.execute({
        operationId: 'proposal_question_partial_update',
        parameters: {
          id,
          data: {
            id,
            text,
            answer: editingValue,
          },
        },
      });

      await refreshProposal();
    } catch (error) {
      setEditingValue(answer);
      fetchErrorHandler(error);
    } finally {
      setIsEditMode(false);
    }
  }, [answer, editingValue, id, refreshProposal, text]);

  return (
    <div className={styles.item}>
      <div
        className={classnames([styles.header, { [styles.isOpen]: isOpen }])}
        onClick={toggle}
      >
        <div className={styles.title}>
          <Typography variant='button' className={styles.count}>
            {index}
          </Typography>

          <Typography>{text}</Typography>
        </div>

        <QuestionHeaderButtons
          isOpen={isOpen}
          isEditMode={isEditMode}
          activateEditMode={activateEditMode}
        />
      </div>

      <CollapseRS isOpen={isOpen}>
        <div
          className={classnames([
            styles.question,
            isEditMode ? styles.editQuestion : styles.viewQuestion,
          ])}
        >
          {!isEditMode ? (
            <LabeledItem label={t`Answer`} value={answer} variant='textarea' />
          ) : (
            <LabeledRichEditor
              wrapperClassName={styles.fullWidth}
              label={t`Answer`}
              value={editingValue}
              onChange={setEditingValue}
            />
          )}

          {isEditMode && (
            <ProposalQuestionButtons {...{ disableEditMode, saveAnswer }} />
          )}
        </div>
      </CollapseRS>
    </div>
  );
};

ProposalQuestion.propTypes = {
  index: PropTypes.number,
  question: PropTypes.shape({
    id: PropTypes.number,
    text: PropTypes.string,
    answer: PropTypes.string,
  }),
};

ProposalQuestion.defaultProps = {
  index: 0,
  question: {},
};

export default memo(ProposalQuestion);
