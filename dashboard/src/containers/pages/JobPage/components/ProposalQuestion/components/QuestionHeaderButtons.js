import React, { memo } from 'react';

import PropTypes from 'prop-types';

import { CLIENT_ADMINISTRATORS, CLIENT_INTERNAL_RECRUITERS } from '@constants';
import { CollapseArrowButton } from '@components';
import { useIsAuthenticatedByRoles } from '@hooks';

import QuestionDropdown from './QuestionDropdown';

import styles from '../ProposalQuestion.module.scss';

const QuestionHeaderButtons = ({ isOpen, isEditMode, activateEditMode }) => {
  const isAdminOrRecruiter = useIsAuthenticatedByRoles([
    CLIENT_ADMINISTRATORS,
    CLIENT_INTERNAL_RECRUITERS,
  ]);

  return (
    <div className={styles.control}>
      <QuestionDropdown
        isEditMode={isEditMode}
        activateEditMode={activateEditMode}
        canUserEdit={isAdminOrRecruiter}
      />
      <CollapseArrowButton isOpen={isOpen} className={styles.collapseArrow} />
    </div>
  );
};

QuestionHeaderButtons.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  isEditMode: PropTypes.bool.isRequired,
  activateEditMode: PropTypes.func.isRequired,
};

export default memo(QuestionHeaderButtons);
