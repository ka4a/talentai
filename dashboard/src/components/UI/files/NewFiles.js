import React, { useCallback } from 'react';

import cloneDeep from 'lodash/cloneDeep';
import PropTypes from 'prop-types';

import FileItem from './FileItem';

const NewFiles = ({
  form,
  filesKey,
  error,
  limit,
  setValue,
  withoutTitle,
  renderCustomTitle,
}) => {
  let files = form[filesKey];

  const onChangeTitle = useCallback(
    (event, id) => {
      if (limit === 1) {
        setValue(filesKey, {
          ...form[filesKey],
          title: event.target.value,
        });
        return;
      }

      const filesCopy = cloneDeep(form[filesKey]);
      const currentFile = filesCopy.find((el) => el.localId === id);
      currentFile.title = event.target.value;

      setValue(filesKey, filesCopy);
    },
    [filesKey, form, setValue, limit]
  );

  const onDeleteFile = useCallback(() => setValue(filesKey, null), [
    setValue,
    filesKey,
  ]);

  const onDeleteFileFromList = useCallback(
    ({ id }) => {
      setValue(
        filesKey,
        files.filter((el) => el.localId !== id)
      );
    },
    [files, setValue, filesKey]
  );

  if (!files) return null;

  if (limit === 1 && files.file) {
    const { file, title } = files;
    return (
      <FileItem
        file={{ ...file, name: file.name, title }}
        {...{ onDeleteFile, onChangeTitle, withoutTitle, renderCustomTitle }}
      />
    );
  }

  return files.map(({ localId, file, title }) => (
    <FileItem
      key={localId}
      file={{ id: localId, name: file.name, title }}
      onDeleteFile={onDeleteFileFromList}
      {...{ onChangeTitle, withoutTitle, renderCustomTitle, error }}
    />
  ));
};

NewFiles.propTypes = {
  form: PropTypes.shape({}).isRequired,
  filesKey: PropTypes.string.isRequired,
  error: PropTypes.string,
  setValue: PropTypes.func.isRequired,
  withoutTitle: PropTypes.bool.isRequired,
  limit: PropTypes.number,
  renderCustomTitle: PropTypes.func,
};

NewFiles.defaultProps = {
  renderCustomTitle: undefined,
  error: null,
};

export default NewFiles;
