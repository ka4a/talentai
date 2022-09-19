import React from 'react';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';

import { useCertifications } from '@hooks';
import { FormSection, DynamicList, LanguageInput, TagsInput } from '@components';

import styles from '../CandidateForm/CandidateForm.module.scss';

const SkillsAndExperience = (props) => {
  const { FormInput, form, setValue, addFieldRow, removeFieldRow } = props;

  const { fields, onAddRow, onRemoveRow } = useCertifications({ ...props });

  return (
    <FormSection id='skills-edit' title={t`Skills & Experience`}>
      <TagsInput
        label={t`Skills`}
        tags={form.tags}
        tagType='candidate'
        onSave={(options) => setValue('tags', options)}
      />

      <hr />

      <LanguageInput
        inputName='languages'
        languages={form.languages}
        {...{ addFieldRow, removeFieldRow, FormInput }}
      />

      <hr />

      <DynamicList
        title={t`Certifications`}
        addRowText={t`+ Add Certification`}
        data={form.certifications}
        {...{ fields, onAddRow, onRemoveRow }}
      />

      <hr />

      <div className={styles.halfWidth}>
        <FormInput
          name='maxNumPeopleManaged'
          label={t`Maximum No. of People Managed`}
        />
      </div>
    </FormSection>
  );
};

SkillsAndExperience.propTypes = {
  FormInput: PropTypes.func.isRequired,
  form: PropTypes.shape({
    tags: PropTypes.array,
    languages: PropTypes.array,
    certifications: PropTypes.array,
  }).isRequired,
  setValue: PropTypes.func.isRequired,
  addFieldRow: PropTypes.func.isRequired,
  removeFieldRow: PropTypes.func.isRequired,
};

export default SkillsAndExperience;
