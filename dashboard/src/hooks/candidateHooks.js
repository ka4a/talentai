import React, { useCallback } from 'react';

import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { CERTIFICATION_CHOICES } from '@constants';
import { useTranslatedChoices } from '@hooks/common';

export const useCertifications = ({
  form,
  FormInput,
  addFieldRow,
  removeFieldRow,
  setValue,
}) => {
  const { i18n } = useLingui();
  const certificationChoices = useTranslatedChoices(i18n, CERTIFICATION_CHOICES);
  const onAddRow = useCallback(() => {
    addFieldRow({
      key: 'certifications',
      defaultObject: { certification: '', certificationOther: '', score: '' },
    });
  }, [addFieldRow]);

  const onRemoveRow = useCallback(
    (event) => {
      removeFieldRow(event, 'certifications');
    },
    [removeFieldRow]
  );

  const onSelectCallback = useCallback(
    (idx) => (selectedOption) => {
      // need to remove certificationOther if 'certification' is not 'other' anymore
      if (selectedOption.value !== 'other') {
        setValue(`certifications[${idx}].certificationOther`, '');
      }
    },
    [setValue]
  );

  const certificationFields = useCallback(
    (idx) => {
      const fields = [
        {
          id: 1,
          render: (idx) => (
            <FormInput
              type='select'
              label={t`Certification`}
              name={`certifications[${idx}].certification`}
              options={certificationChoices}
              onSelectCallback={onSelectCallback(idx)}
            />
          ),
        },
        {
          id: 2,
          render: (idx) => (
            <FormInput
              label={t`Score or Level`}
              name={`certifications[${idx}].score`}
            />
          ),
        },
      ];

      if (form.certifications[idx].certification === 'other') {
        fields.splice(1, 0, {
          id: 3,
          render: (idx) => (
            <FormInput
              label={t`Certification Name`}
              name={`certifications[${idx}].certificationOther`}
            />
          ),
        });
      }

      return fields;
    },
    [form.certifications, certificationChoices, onSelectCallback]
  );

  return {
    fields: certificationFields,
    onAddRow,
    onRemoveRow,
  };
};
