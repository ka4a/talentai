import React from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { useLingui } from '@lingui/react';
import { t } from '@lingui/macro';

import { FormSection, LanguageInput, TagsInput } from '@components';
import { EDUCATION_LEVELS_CHOICES } from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from '../JobForm/JobForm.module.scss';

const Requirements = (props) => {
  const { FormInput, form, setValue, addFieldRow, removeFieldRow } = props;

  const workExperienceOptions = useSelector(
    (state) => state.settings.localeData.workExperiences
  );

  const { i18n } = useLingui();
  const educationLevelsChoices = useTranslatedChoices(i18n, EDUCATION_LEVELS_CHOICES);

  return (
    <FormSection id='requirements-edit' title={t`Requirements`}>
      <FormInput
        type='rich-editor'
        name='requirements'
        label={i18n._(t`Requirements`)}
        required
      />

      <hr />

      <div className={classnames([styles.rowWrapper, styles.twoElements])}>
        <FormInput
          type='select'
          name='educationalLevel'
          label={i18n._(t`Education Level`)}
          options={educationLevelsChoices}
          clearable
        />
        <FormInput
          type='select'
          name='workExperience'
          label={i18n._(t`Work Experience`)}
          options={workExperienceOptions}
          labelKey='label'
          clearable
        />
      </div>

      <div className={styles.skills}>
        <TagsInput
          label={t`Skills`}
          tags={form.skills}
          tagType='skill'
          onSave={(options) => setValue('skills', options)}
        />
      </div>

      <hr />

      <LanguageInput
        inputName='requiredLanguages'
        languages={form.requiredLanguages}
        removeFieldRow={removeFieldRow}
        addFieldRow={addFieldRow}
        FormInput={FormInput}
      />
    </FormSection>
  );
};

Requirements.propTypes = {
  FormInput: PropTypes.func.isRequired,
  form: PropTypes.shape({}).isRequired,
  setValue: PropTypes.func.isRequired,
  addFieldRow: PropTypes.func.isRequired,
  removeFieldRow: PropTypes.func.isRequired,
};

export default Requirements;
