import React from 'react';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { useCertifications } from '@hooks';
import { DynamicList, LanguageInput } from '@components';

const SkillsSection = (props) => {
  const { FormInput, form, addFieldRow, removeFieldRow } = props;

  const { fields, onAddRow, onRemoveRow } = useCertifications({ ...props });

  return (
    <>
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
    </>
  );
};

SkillsSection.propTypes = {
  FormInput: PropTypes.func.isRequired,
  form: PropTypes.shape({
    languages: PropTypes.array,
    certifications: PropTypes.array,
  }).isRequired,
  setValue: PropTypes.func.isRequired,
  addFieldRow: PropTypes.func.isRequired,
  removeFieldRow: PropTypes.func.isRequired,
};

export default SkillsSection;
