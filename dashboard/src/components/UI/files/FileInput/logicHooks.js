import { useCallback, useMemo } from 'react';

import cloneDeep from 'lodash/cloneDeep';
import snakeCase from 'lodash/snakeCase';
import { v4 as uuid } from 'uuid';

import { client } from '@client';
import { fetchErrorHandler, downloadFile, isDialogCanceled } from '@utils';

import openDeleteFile from '../dialogs/openDeleteFile';
import { FILE_TYPES, OTHER_FILES_TYPES } from './constants';

const getAcceptedFileType = (acceptedFileType) =>
  FILE_TYPES[acceptedFileType] || OTHER_FILES_TYPES;

const useUploadedFiles = (props) => {
  const {
    form,
    filesKey,
    setValue,
    readOperationId,
    deleteOperationId,
    limit,
    ftype,
    isResume,
  } = props;

  const uploadedFiles = useMemo(() => {
    const localFiles = form[filesKey];
    if (limit !== 1) return localFiles;
    return localFiles !== null ? [{ id: form.id, file: localFiles }] : [];
  }, [filesKey, form, limit]);

  const onChangeTitle = useCallback(
    (event, id) => {
      const filesCopy = cloneDeep(form[filesKey]);
      const currentFile = filesCopy.find((el) => el.id === id);
      currentFile.title = event.target.value;

      // needed for determining for what files need to call PATCH endpoint
      currentFile.changed = true;

      setValue(filesKey, filesCopy);
    },
    [filesKey, form, setValue]
  );

  const onDownloadFile = useCallback(
    // customFtype is available for candidate resume
    (fileId, customFtype) =>
      downloadFile(readOperationId, customFtype ?? ftype, fileId),
    [ftype, readOperationId]
  );

  const onDeleteFile = useCallback(
    // localId and customFtype are available for candidate resume
    async ({ id, localId, ftype: customFtype, file }) => {
      if (await isDialogCanceled(openDeleteFile())) return;

      try {
        const finalFtype = customFtype ?? ftype;

        // send request either if it's not a resume or if it is uploaded resume
        if (!isResume || (isResume && file)) {
          await client.execute({
            operationId: deleteOperationId,
            parameters: { id, ftype: finalFtype ? snakeCase(finalFtype) : '' },
          });
        }

        const IDKey = isResume ? 'localId' : 'id';
        const IDField = isResume ? localId : id;
        const data =
          limit === 1 ? null : form[filesKey].filter((file) => file[IDKey] !== IDField);

        setValue(filesKey, data);
      } catch (error) {
        fetchErrorHandler(error);
      }
    },
    [ftype, isResume, limit, form, filesKey, setValue, deleteOperationId]
  );

  return {
    uploadedFiles,
    onChangeTitle,
    onDownloadFile,
    onDeleteFile,
  };
};

function useOnDrop({ isResume, limit, form, newFilesKey, setValue }) {
  // triggers on picking file via single click as well
  return useCallback(
    (acceptedFiles) => {
      let filesToBeAdded;
      if (isResume) {
        filesToBeAdded = acceptedFiles.map((file) => ({
          localId: uuid(),
          ftype: '',
          fileObject: file,
          name: file.name,
          error: false,
        }));
      } else {
        filesToBeAdded = acceptedFiles.map((file) => ({
          localId: uuid(),
          file,
          title: '',
          uploaded: false,
          error: false,
        }));
      }

      const data =
        limit === 1 ? filesToBeAdded[0] : [...form[newFilesKey], ...filesToBeAdded];

      setValue(newFilesKey, data);
    },
    // eslint-disable-next-line no-undef
    [isResume, limit, form, newFilesKey, setValue]
  );
}

const useIsLimitReached = ({ limit, form, filesKey, newFilesKey, isResume }) => {
  const uploadedFiles = form[filesKey];
  const newFiles = form[newFilesKey];

  return useMemo(() => {
    let isLimitReached = limit === 1 && Boolean(uploadedFiles || newFiles);

    if (isResume) isLimitReached = uploadedFiles?.length === limit || isLimitReached;

    return isLimitReached;
  }, [isResume, limit, newFiles, uploadedFiles]);
};

export { useIsLimitReached, useUploadedFiles, useOnDrop, getAcceptedFileType };
