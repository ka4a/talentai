import React, { memo } from 'react';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { getFileName, getFileExtension, deleteFile, downloadFile } from '@utils';
import { FILE_TYPES } from '@components/UI/files/FileInput/constants';
import { FormSection, FileThumbnail } from '@components';

import styles from './JobDetailsSections.module.scss';

const Attachments = ({ job, refreshJob }) => {
  return (
    <FormSection id='job-attachments' titleVariant='subheading' title={t`Attachments`}>
      <div className={styles.flexWrap}>
        {job.files.map(
          ({ id, title, file, thumbnail }) =>
            file && (
              <FileThumbnail
                key={title + id}
                file={file}
                id={id}
                title={title || getFileName(file)}
                thumbnail={
                  FILE_TYPES.image.includes('.' + getFileExtension(file))
                    ? file
                    : thumbnail || ''
                }
                onDownload={() => downloadFile('job_files_read', null, id)}
                onRemove={(id) => deleteFile(id, null, refreshJob, 'job_files_delete')}
              />
            )
        )}
      </div>
    </FormSection>
  );
};

Attachments.propTypes = {
  job: PropTypes.object.isRequired,
  refreshJob: PropTypes.func.isRequired,
};

export default memo(Attachments);
