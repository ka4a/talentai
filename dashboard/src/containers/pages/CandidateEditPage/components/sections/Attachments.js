import React, { memo } from 'react';

import { t } from '@lingui/macro';

import {
  FileInput,
  FormImageCropInput,
  FormSection,
  ResumeInput,
  Typography,
} from '@components';

import styles from '../CandidateForm/CandidateForm.module.scss';

const renderSubheading = (text) => (
  <Typography variant='subheading' className={styles.subheading}>
    {text}
  </Typography>
);

const Attachments = ({ form, setValue, errors }) => (
  <FormSection id='attachments-edit' title={t`Attachments`}>
    <div className={styles.attachmentWrapper}>
      {renderSubheading(t`Resume`)}
      <ResumeInput {...{ form, setValue }} />
    </div>

    <div className={styles.attachmentWrapper}>
      {renderSubheading(t`Photo`)}
      <FormImageCropInput
        form={form}
        setValue={setValue}
        errors={errors}
        downloadOperationId='candidates_get_file'
        deleteOperationId='candidates_delete_file'
        ftype='photo'
        fileKey='photo'
        newFileKey='newPhoto'
      />
    </div>

    <div className={styles.attachmentWrapper}>
      {renderSubheading(t`Other`)}
      <FileInput
        form={form}
        setValue={setValue}
        readOperationId='candidate_misc_file_read'
        deleteOperationId='candidate_misc_file_delete'
        filesKey='files'
        newFilesKey='newFiles'
        errorFilesKey='filesError'
        acceptedFileType='other'
      />
    </div>
  </FormSection>
);

export default memo(Attachments);
