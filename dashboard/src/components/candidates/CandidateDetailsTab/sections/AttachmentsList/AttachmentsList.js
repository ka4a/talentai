import React, { memo, useCallback } from 'react';

import { t } from '@lingui/macro';

import { useGetCandidate } from '@swrAPI';
import { FileThumbnail } from '@components';
import { getFileName, downloadFile } from '@utils';

import styles from './AttachmentsList.module.scss';

const AttachmentsList = () => {
  const { data } = useGetCandidate();
  const { id, resume, resumeJa, cvJa, files } = data;

  const downloadOtherFile = useCallback(
    (id) => downloadFile('candidate_misc_file_read', null, id),
    []
  );

  const singleFiles = [
    { title: t`English Resume`, file: resume, fileKey: 'resume' },
    { title: t`Japanese Resume (Rirekisho)`, file: resumeJa, fileKey: 'resume_ja' },
    { title: t`Japanese CV (Shokumu-keirekisho)`, file: cvJa, fileKey: 'cv_ja' },
  ];

  return (
    <div className={styles.fileWrapper}>
      {singleFiles.map(
        ({ file, title, fileKey }) =>
          file && (
            <FileThumbnail
              id={id}
              file={file}
              title={title}
              key={id + title}
              onDownload={() => downloadFile('candidates_get_file', fileKey, id)}
            />
          )
      )}

      {files.map(
        ({ id, title, file }) =>
          file && (
            <FileThumbnail
              id={id}
              file={file}
              key={title + id}
              title={title || getFileName(file)}
              onDownload={() => downloadOtherFile(id)}
            />
          )
      )}
    </div>
  );
};

export default memo(AttachmentsList);
