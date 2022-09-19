import React, { useCallback } from 'react';

import PropTypes from 'prop-types';

import ThumbnailList from '../ThumbnailList';

FormThumbnailList.propTypes = {
  form: PropTypes.object.isRequired,
  name: PropTypes.string.isRequired,
  setValue: PropTypes.func.isRequired,
  newFilesName: PropTypes.string,
  renderActions: PropTypes.func,

  params: PropTypes.object,
  fetchOperationId: PropTypes.string.isRequired,
  previewOperationId: PropTypes.string,
  deleteOperationId: PropTypes.string,
};

FormThumbnailList.defaultProps = {
  params: null,
};

function FormThumbnailList(props) {
  const {
    form,
    name,
    setValue,
    newFilesName,
    renderActions,

    params,
    fetchOperationId,
    previewOperationId,
    deleteOperationId,
    onRemoved,
  } = props;

  const newFiles = form[newFilesName];

  const removeNewFile = useCallback(
    (localId) => {
      setValue(
        newFilesName,
        newFiles.filter((e) => e.localId !== localId)
      );
    },
    [setValue, newFilesName, newFiles]
  );

  return (
    <ThumbnailList
      files={form[name]}
      newFiles={newFiles}
      onNewFileRemoved={removeNewFile}
      onFileRemoved={onRemoved}
      params={params}
      fetchOperationId={fetchOperationId}
      previewOperationId={previewOperationId}
      deleteOperationId={deleteOperationId}
      renderActions={renderActions}
    />
  );
}

export default FormThumbnailList;
