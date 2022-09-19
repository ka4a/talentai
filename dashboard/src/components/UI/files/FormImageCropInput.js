import React, { memo, useCallback } from 'react';

import PropTypes from 'prop-types';

import { client } from '@client';
import { downloadFile, fetchErrorHandler } from '@utils';

import ImageCropInput from './ImageCropInput';

function FormImageCropInput(props) {
  const {
    setValue,
    fileKey,
    newFileKey,
    deleteOperationId,
    downloadOperationId,
    form,
    errors,
    ftype,
  } = props;

  const handleChangeNewFile = useCallback(
    (file) => {
      setValue(newFileKey, { uploaded: false, file });
    },
    [newFileKey, setValue]
  );

  const handleDeleteNewFile = useCallback(() => setValue(newFileKey, null), [
    newFileKey,
    setValue,
  ]);

  const fileId = form.id;
  const handleDelete = useCallback(async () => {
    try {
      await deleteFile(deleteOperationId, ftype, fileId);
      setValue(fileKey, null);
    } catch (error) {
      fetchErrorHandler(error);
    }
  }, [deleteOperationId, setValue, fileKey, fileId, ftype]);

  const handleDownload = useHandleDownload(downloadOperationId, fileId, ftype);

  return (
    <ImageCropInput
      onDeleteFile={handleDelete}
      onDownloadFile={handleDownload}
      onChangeNewFile={handleChangeNewFile}
      onDeleteNewFile={handleDeleteNewFile}
      fileUrl={form[fileKey]}
      newFile={form[newFileKey]?.file}
      errors={errors?.[fileKey]}
    />
  );
}

FormImageCropInput.propTypes = {
  form: PropTypes.object.isRequired,
  errors: PropTypes.object,
  filesKey: PropTypes.string.isRequired,
  newFilesKey: PropTypes.string.isRequired,
  ftype: PropTypes.string,
  setValue: PropTypes.func.isRequired,
  deleteOperationId: PropTypes.string,
  downloadOperationId: PropTypes.string,
};

function deleteFile(operationId, ftype, id) {
  return client.execute({ operationId, parameters: { id, ftype } });
}

function useHandleDownload(downloadOperationId, id, type) {
  const handleDownloadFile = useCallback(
    () => downloadFile(downloadOperationId, type, id),
    [downloadOperationId, id, type]
  );

  return downloadOperationId ? handleDownloadFile : null;
}

export default memo(FormImageCropInput);
