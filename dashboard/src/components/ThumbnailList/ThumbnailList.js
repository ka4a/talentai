import React, { memo, useCallback, useState } from 'react';
import { FcDownload } from 'react-icons/fc';

import PropTypes from 'prop-types';
import fileDownload from 'js-file-download';

import { client } from '@client';
import { fetchErrorHandler, handleRequestError, getFileName } from '@utils';

import FileThumbnail from '../FileThumbnail/FileThumbnail';
import NewFileThumbnail from '../NewFileThumbnail';
import FilePreviewModal from '../UI/files/FilePreviewModal';

import styles from './ThumbnailList.module.scss';

const ThumbnailList = (props) => {
  const {
    deleteOperationId,
    onFileRemoved,
    ftype,
    fetchOperationId,
    params,
    files,
    previewOperationId,
    onNewFileRemoved,
    newFiles,
    renderActions,
    type,
  } = props;

  const [removedThumbnails, setRemovedThumbnails] = useState([]);

  const handleRemove = useCallback(
    async (id) => {
      if (!deleteOperationId) return;

      try {
        await client.execute({
          operationId: deleteOperationId,
          parameters: { id },
        });

        setRemovedThumbnails((prevThumbnails) => [...prevThumbnails, id]);
        if (onFileRemoved) onFileRemoved(id);
      } catch (error) {
        fetchErrorHandler(error);
      }
    },
    [deleteOperationId, onFileRemoved]
  );

  const handleDownload = useCallback(
    async (id) => {
      try {
        const { text, headers } = await client.execute({
          operationId: fetchOperationId,
          parameters: { id, ftype, ...params },
        });

        fileDownload(text, headers['content-disposition'].split('"')[1]);
      } catch (error) {
        handleRequestError(error, 'get');
      }
    },
    [fetchOperationId, ftype, params]
  );

  const filteredFiles = files.filter((file) => !removedThumbnails.includes(file.id));

  return (
    <div className={styles.thumbnailList}>
      {filteredFiles.map((file) => {
        const { id, title, file: fileItem } = file;

        if (type === 'withButton') {
          return (
            <div key={id} className={styles.fileWrapper}>
              <p className={styles.fileName}>{title || getFileName(fileItem)}</p>

              <button
                className={styles.downloadButton}
                onClick={() => handleDownload(id)}
              >
                <FcDownload />
              </button>
            </div>
          );
        }

        return (
          <FilePreviewModal
            {...file}
            key={id}
            operationId={fetchOperationId}
            previewOperationId={previewOperationId}
            params={params}
            ftype={ftype}
            onDownload={handleDownload}
          >
            <FileThumbnail
              {...file}
              onDownload={handleDownload}
              onRemove={deleteOperationId ? handleRemove : null}
            >
              {renderActions?.(id)}
            </FileThumbnail>
          </FilePreviewModal>
        );
      })}

      {newFiles.map(({ localId, uploaded, error, file }, i) => (
        <NewFileThumbnail
          file={file.name}
          uploaded={uploaded}
          onRemove={onNewFileRemoved}
          error={error}
          key={localId}
          id={localId}
        >
          {renderActions?.(localId, true)}
        </NewFileThumbnail>
      ))}
    </div>
  );
};

ThumbnailList.propTypes = {
  files: PropTypes.array.isRequired,
  onNewFileRemoved: PropTypes.func,
  onFileRemoved: PropTypes.func,
  newFiles: PropTypes.array,
  params: PropTypes.object,
  fetchOperationId: PropTypes.string.isRequired,
  previewOperationId: PropTypes.string,
  deleteOperationId: PropTypes.string,
  renderActions: PropTypes.func,
  type: PropTypes.string,
};

ThumbnailList.defaultProps = {
  onNewFileRemoved: null,
  files: [],
  newFiles: [],
  params: null,
};

export default memo(ThumbnailList);
