import React, { useEffect } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { useStaffOptions } from '@swrAPI';
import { FormSection } from '@components';
import { CANDIDATE_SOURCE_CHOICES, PLATFORM_CHOICES } from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from '../CandidateForm/CandidateForm.module.scss';

const CandidateManagement = ({ source, platform, FormInput, setValue }) => {
  const { i18n } = useLingui();
  const candidateSourceChoices = useTranslatedChoices(i18n, CANDIDATE_SOURCE_CHOICES);
  const platformChoices = useTranslatedChoices(i18n, PLATFORM_CHOICES);

  const staffList = useStaffOptions();

  const isSourceOther = source === 'Other';
  const isPlatformOther = platform === 'other';

  useEffect(() => {
    // reset 'sourceDetails' when changing source away from 'other'
    if (!isSourceOther) setValue('sourceDetails', '');
  }, [isSourceOther, setValue]);

  return (
    <FormSection id='candidate-management-edit' title={t`Candidate Management`}>
      <div className={classnames([styles.rowWrapper, styles.threeElements])}>
        <FormInput
          type='select'
          name='source'
          label={t`Source`}
          options={candidateSourceChoices}
          clearable
        />
        <FormInput
          type='select'
          name='platform'
          label={t`Platform`}
          options={platformChoices}
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

      {isPlatformOther && (
        <div className={styles.topGap}>
          <FormInput name='platformOtherDetails' label={t`Platform Other`} />
        </div>
      )}

      <FormInput
        type='rich-editor'
        name='note'
        wrapperClassName={styles.topGap}
        label={t`Candidate Notes`}
      />
    </FormSection>
  );
};

CandidateManagement.propTypes = {
  source: PropTypes.string.isRequired,
  platform: PropTypes.string.isRequired,
  FormInput: PropTypes.func.isRequired,
  setValue: PropTypes.func.isRequired,
};

export default CandidateManagement;
