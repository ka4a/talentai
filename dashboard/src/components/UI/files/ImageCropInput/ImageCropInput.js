import React, { useCallback, useMemo, useState, memo } from 'react';

import PropTypes from 'prop-types';

import { isDialogCanceled } from '@utils';

import openDeleteFile from '../dialogs/openDeleteFile';
import FileItem from '../FileItem';
import Dropzone from '../Dropzone';
import ModalCropImage from '../ModalCropImage';

function ImageCropInput(props) {
  const {
    onDownloadFile,
    onDeleteFile,
    onDeleteNewFile,
    onChangeNewFile,
    error,
    newFile,
    fileUrl,
  } = props;

  const fileWrapper = useMemo(() => ({ file: fileUrl }), [fileUrl]);

  const handleDeleteFile = useCallback(async () => {
    if (await isDialogCanceled(openDeleteFile())) return;
    onDeleteFile?.();
  }, [onDeleteFile]);

  const [fileToCrop, setFileToCrop] = useState(null);

  const handleDrop = useCallback((files) => {
    setFileToCrop(files[0]);
  }, []);

  const handleCloseModal = useCallback(() => {
    setFileToCrop(null);
  }, []);

  const handleSaveModal = useCallback(
    (file) => {
      onChangeNewFile(file);
      setFileToCrop(null);
    },
    [onChangeNewFile]
  );

  const commonFileItemProps = { withoutTitle: true, error };

  let filePreview;
  if (fileUrl) {
    filePreview = (
      <FileItem
        {...commonFileItemProps}
        file={fileWrapper}
        onDeleteFile={handleDeleteFile}
        onDownloadFile={onDownloadFile}
      />
    );
  } else if (newFile) {
    filePreview = (
      <FileItem
        {...commonFileItemProps}
        isNewFile
        file={newFile}
        onDeleteFile={onDeleteNewFile}
      />
    );
  } else {
    filePreview = <Dropzone acceptedFileType='image' onDrop={handleDrop} />;
  }

  return (
    <div>
      {filePreview}
      <ModalCropImage
        file={fileToCrop}
        isOpen={fileToCrop != null}
        onClose={handleCloseModal}
        onSave={handleSaveModal}
      />
    </div>
  );
}

ImageCropInput.propTypes = {
  fileUrl: PropTypes.string,
  newFile: PropTypes.instanceOf(File),
  onDeleteFile: PropTypes.func,
  onDownloadFile: PropTypes.func,
  onChangeNewFile: PropTypes.func,
  onDeleteNewFile: PropTypes.func,
  error: PropTypes.string,
};

export default memo(ImageCropInput);
