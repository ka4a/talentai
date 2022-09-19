import React, { memo } from 'react';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { Button } from '@components';

import styles from '../ProposalQuestion.module.scss';

const QuestionButtons = ({ disableEditMode, saveAnswer }) => {
  return (
    <div className={styles.questionButtons}>
      <Button variant='secondary' onClick={disableEditMode} className='mr-3'>
        <Trans>Cancel</Trans>
      </Button>

      <Button variant='primary' onClick={saveAnswer}>
        <Trans>Save</Trans>
      </Button>
    </div>
  );
};

QuestionButtons.propTypes = {
  disableEditMode: PropTypes.func,
  saveAnswer: PropTypes.func,
};

export default memo(QuestionButtons);
