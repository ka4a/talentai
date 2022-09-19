import React, { useCallback, useMemo } from 'react';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { LANGUAGE_CHOICES, LANGUAGE_LEVEL_CHOICES } from '@constants';
import { useTranslatedChoices } from '@hooks';

import DynamicList from '../DynamicList';

const LanguageInput = (props) => {
  const { languages, inputName, FormInput, addFieldRow, removeFieldRow } = props;

  const { i18n } = useLingui();
  const languageChoices = useTranslatedChoices(i18n, LANGUAGE_CHOICES);
  const languageLevelChoices = useTranslatedChoices(i18n, LANGUAGE_LEVEL_CHOICES);

  const getRemainingLanguages = useCallback(
    (current) => {
      const languageCodes = languages.map((el) => el.language);
      return languageChoices.filter(
        (el) => current?.language === el.value || !languageCodes.includes(el.value)
      );
    },
    [languages, languageChoices]
  );

  const onAddLanguage = useCallback(() => {
    addFieldRow({
      key: inputName,
      defaultObject: { language: null, level: null },
    });
  }, [addFieldRow, inputName]);

  const onRemoveLanguage = useCallback(
    (event) => {
      removeFieldRow(event, inputName);
    },
    [inputName, removeFieldRow]
  );

  const fields = useMemo(
    () => [
      {
        id: 1,
        render: (idx, language) => (
          <FormInput
            type='select'
            label={t`Language`}
            name={`${inputName}[${idx}].language`}
            options={getRemainingLanguages(language)}
            placeholder={t`No language selected`}
            isSearchable
          />
        ),
      },
      {
        id: 2,
        render: (idx) => (
          <FormInput
            type='select'
            label={t`Fluency Level`}
            name={`${inputName}[${idx}].level`}
            options={languageLevelChoices}
            placeholder={t`No level selected`}
          />
        ),
      },
    ],
    [getRemainingLanguages, inputName, languageLevelChoices]
  );

  return (
    <DynamicList
      title={t`Languages`}
      data={languages}
      fields={fields}
      onAddRow={onAddLanguage}
      onRemoveRow={onRemoveLanguage}
      addRowText={t`+ Add Language`}
    />
  );
};

LanguageInput.propTypes = {
  inputName: PropTypes.string.isRequired,
  languages: PropTypes.array.isRequired,
  addFieldRow: PropTypes.func.isRequired,
  removeFieldRow: PropTypes.func.isRequired,
  FormInput: PropTypes.elementType.isRequired,
};

export default LanguageInput;
