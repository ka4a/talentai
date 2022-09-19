import React from 'react';

import PropTypes from 'prop-types';

import NewFiles from '../NewFiles';
import FileItem from '../FileItem';
import Dropzone from '../Dropzone';
import { useIsLimitReached, useUploadedFiles, useOnDrop } from './logicHooks';

const FileInput = (props) => {
  const {
    form,
    setValue,
    filesKey,
    newFilesKey,
    errorFilesKey,
    acceptedFileType,
    withoutNewFilesList,
    withoutTitle,
    fileMaxSize,
    renderCustomTitle,
    limit,
    isResume,
    readOperationId,
  } = props;

  const isLimitReached = useIsLimitReached({
    limit,
    form,
    filesKey,
    newFilesKey,
    isResume,
  });

  const { uploadedFiles, onDownloadFile, ...filesHandlers } = useUploadedFiles({
    ...props,
  });

  const onDrop = useOnDrop(props);

  const checkIfDownloadable = (file) => (!isResume || file) && readOperationId;

  return (
    <>
      {uploadedFiles.map((file) => (
        <FileItem
          file={file}
          withoutTitle={withoutTitle}
          renderCustomTitle={renderCustomTitle}
          // file.localId is needed for resume, because all resume have id - candidateId
          key={file.localId ?? file.id}
          // disable downloading for newly added resume
          onDownloadFile={checkIfDownloadable(file.file) ? onDownloadFile : null}
          error={form[errorFilesKey]}
          {...filesHandlers}
        />
      ))}

      {!withoutNewFilesList && (
        <NewFiles
          form={form}
          limit={limit}
          setValue={setValue}
          filesKey={newFilesKey}
          error={form[errorFilesKey]}
          withoutTitle={withoutTitle}
          renderCustomTitle={renderCustomTitle}
        />
      )}

      {!isLimitReached && (
        <Dropzone
          onDrop={onDrop}
          fileMaxSize={fileMaxSize}
          acceptedFileType={acceptedFileType}
          limit={limit}
        />
      )}
    </>
  );
};

FileInput.propTypes = {
  form: PropTypes.shape({}).isRequired,
  setValue: PropTypes.func.isRequired,
  readOperationId: PropTypes.string,
  deleteOperationId: PropTypes.string,
  ftype: PropTypes.string,
  filesKey: PropTypes.string.isRequired,
  newFilesKey: PropTypes.string,
  errorFilesKey: PropTypes.string,
  acceptedFileType: PropTypes.oneOf(['image', 'resume', 'other']),
  fileMaxSize: PropTypes.number,
  withoutNewFilesList: PropTypes.bool,
  withoutTitle: PropTypes.bool,
  renderCustomTitle: PropTypes.func,
  limit: PropTypes.number,
  isResume: PropTypes.bool,
};

FileInput.defaultProps = {
  withoutNewFilesList: false,
  withoutTitle: false,
  acceptedFileType: 'other',
  newFilesKey: '',
  errorFilesKey: '',
  renderCustomTitle: undefined,
  limit: null,
  isResume: false,
};

export default FileInput;
