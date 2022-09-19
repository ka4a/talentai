import React, { useCallback } from 'react';

import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';
import { useLingui } from '@lingui/react';

import { useGetJob } from '@swrAPI';
import { Typography } from '@components';
import { DECISION_CHOICES } from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from '../InterviewAssessmentModal.module.scss';

const Inputs = ({ FormInput, setValue }) => {
  const { i18n } = useLingui();
  const decisionChoices = useTranslatedChoices(i18n, DECISION_CHOICES);

  const { data: job } = useGetJob();

  const resetRating = useCallback(
    (criteriaId) => {
      setValue(`hiringCriteria[${criteriaId}]`, null);
    },
    [setValue]
  );

  return (
    <div className={styles.contentWrapper}>
      <FormInput type='rich-editor' label={t`Assessment Notes`} name='notes' />

      <hr />

      <Typography variant='subheading'>
        <Trans>Hiring Criteria</Trans>
      </Typography>

      <div className={classnames([styles.rowWrapper, styles.topGap, styles.criteria])}>
        {job.hiringCriteria.map((criteria) => (
          <FormInput
            type='rating'
            key={criteria.id}
            label={criteria.name}
            name={`hiringCriteria[${criteria.id}]`}
            resetRating={() => resetRating(criteria.id)}
          />
        ))}
      </div>

      <hr />

      <div className={classnames([styles.row, styles.topGap, styles.decision])}>
        <FormInput
          type='select'
          name='decision'
          label={t`Decision`}
          options={decisionChoices}
          menuPlacement='top'
          required
        />
      </div>
    </div>
  );
};

Inputs.propTypes = {
  FormInput: PropTypes.func.isRequired,
  setValue: PropTypes.func.isRequired,
};

export default Inputs;
