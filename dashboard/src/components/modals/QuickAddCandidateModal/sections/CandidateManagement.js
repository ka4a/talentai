import React, { useEffect } from 'react';

import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';
import { useLingui } from '@lingui/react';

import { useStaffOptions } from '@swrAPI';
import { Typography } from '@components';
import { CANDIDATE_SOURCE_CHOICES } from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from '../QuickAddCandidateModal.module.scss';

const CandidateManagement = ({ source, setValue, FormInput }) => {
  const { i18n } = useLingui();
  const candidateSourceChoices = useTranslatedChoices(i18n, CANDIDATE_SOURCE_CHOICES);

  const staffList = useStaffOptions();

  const isSourceOther = source === 'Other';

  useEffect(() => {
    // reset 'sourceDetails' when changing source away from 'other'
    if (!isSourceOther) setValue('sourceDetails', '');
  }, [isSourceOther, setValue]);

  return (
    <>
      <Typography
        variant='subheading'
        className={classnames([styles.subtitle, styles.topGap])}
      >
        <Trans>Candidate Management</Trans>
      </Typography>

      <div className={classnames([styles.rowWrapper, styles.twoElements])}>
        <FormInput
          type='select'
          name='source'
          label={t`Source`}
          options={candidateSourceChoices}
          clearable
        />
        <FormInput
          type='select'
          name='owner'
          label={t`Sourced By`}
          options={staffList}
          searchable
          clearable
        />
      </div>

      {isSourceOther && (
        <div className={styles.topGap}>
          <FormInput name='sourceDetails' label={t`Source Details`} />
        </div>
      )}
    </>
  );
};

CandidateManagement.propTypes = {
  source: PropTypes.string.isRequired,
  setValue: PropTypes.func.isRequired,
  FormInput: PropTypes.func.isRequired,
};

export default CandidateManagement;
