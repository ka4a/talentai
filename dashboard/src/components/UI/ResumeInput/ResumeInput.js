import React, { memo, useCallback } from 'react';

import { t, defineMessage } from '@lingui/macro';
import cloneDeep from 'lodash/cloneDeep';
import differenceBy from 'lodash/differenceBy';
import PropTypes from 'prop-types';
import { useLingui } from '@lingui/react';

import { useTranslatedChoices } from '@hooks';

import Typography from '../Typography';
import FileInput from '../files/FileInput';
import LabeledSelect from '../LabeledInputs/LabeledSelect';

import styles from './ResumeInput.module.scss';

const ALL_RESUME = [
  { ftype: 'resume', name: defineMessage({ message: 'English Resume' }).id },
  {
    ftype: 'resumeJa',
    name: defineMessage({ message: 'Japanese Resume (Rirekisho)' }).id,
  },
  {
    ftype: 'cvJa',
    name: defineMessage({ message: 'Japanese CV (Shokumu-keirekisho)' }).id,
  },
];

/**
 * ResumeInput requires 'allResume' field in the 'form' object
 * it will collect all resume in there
 * when form is submitted it should be processed manually
 */
const ResumeInput = ({ form, setValue }) => {
  const { i18n } = useLingui();
  const resumeChoices = useTranslatedChoices(i18n, ALL_RESUME);
  const getAvailableOptions = useCallback(
    (selectedOption) => {
      return differenceBy(
        resumeChoices,
        form.allResume.filter((el) => el.ftype !== selectedOption),
        'ftype'
      );
    },
    [form.allResume, resumeChoices]
  );

  const onSelectResumeType = useCallback(
    (prevOption, newOption, id) => {
      const resumeCopy = cloneDeep(form.allResume);

      const file = resumeCopy.find((el) => el.localId === id);
      file.ftype = newOption;

      setValue('allResume', resumeCopy);
    },
    [form.allResume, setValue]
  );

  return (
    <FileInput
      form={form}
      setValue={setValue}
      readOperationId='candidates_get_file'
      deleteOperationId='candidates_delete_file'
      filesKey='allResume'
      newFilesKey='allResume'
      acceptedFileType='resume'
      withoutNewFilesList
      limit={3}
      isResume
      renderCustomTitle={({ ftype, localId }) => (
        <div className={styles.resumeSelect}>
          <LabeledSelect
            label={t`Type`}
            value={ftype}
            onChange={(newOption) => onSelectResumeType(ftype, newOption, localId)}
            options={getAvailableOptions(ftype)}
            valueKey='ftype'
            isDisabled={
              // disable if this is uploaded file, not new one
              form.allResume.find((el) => el.ftype === ftype)?.file
            }
          />

          {!ftype && form.resumeError && (
            <Typography variant='caption' className={styles.error}>
              {form.resumeError}
            </Typography>
          )}
        </div>
      )}
    />
  );
};

ResumeInput.propTypes = {
  form: PropTypes.shape({}).isRequired,
  setValue: PropTypes.func.isRequired,
};

export default memo(ResumeInput);
