import React, { memo } from 'react';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';

import { FileInput, FormSection } from '@components';

import styles from '../JobForm/JobForm.module.scss';

const Attachments = ({ form, setValue }) => (
  <FormSection id='attachments-edit' title={t`Attachments`}>
    <div className={styles.attachments}>
      <FileInput
        form={form}
        setValue={setValue}
        readOperationId='job_files_read'
        deleteOperationId='job_files_delete'
        filesKey='files'
        newFilesKey='newFiles'
        acceptedFileType='other'
      />
    </div>
  </FormSection>
);

Attachments.propTypes = {
  form: PropTypes.shape({}).isRequired,
  setValue: PropTypes.func.isRequired,
};

export default memo(Attachments);
