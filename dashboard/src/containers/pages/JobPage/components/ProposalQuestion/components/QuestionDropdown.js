import React, { memo } from 'react';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { ActionsDropdown } from '@components';

import styles from '../ProposalQuestion.module.scss';

const createOption = (text, handler) => ({ text, handler });

const QuestionDropdown = ({ isEditMode, activateEditMode, canUserEdit }) => {
  const actions = [];

  if (canUserEdit && !isEditMode) {
    actions.push(createOption(t`Edit Answer`, activateEditMode));
  }

  if (actions.length < 1) return null;

  return (
    <div className={styles.headerItem}>
      <ActionsDropdown actions={actions} />
    </div>
  );
};

QuestionDropdown.propTypes = {
  isEditMode: PropTypes.bool.isRequired,
  activateEditMode: PropTypes.func.isRequired,
  canUserEdit: PropTypes.bool.isRequired,
};

export default memo(QuestionDropdown);
