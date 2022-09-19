import { t } from '@lingui/macro';

import { client } from '@client';

const isUploaded = (e) => e.file.uploaded;
const isError = (e) => e.file.error;

const makeSaveFilesForForm = (getUploads, getStatePatch) => async (
  callback,
  obj, // this is the server response
  formState,
  throwErrorMessage
) => {
  // upload single file and set "uploaded" and "error" statuses depending on response
  const upload = async (options) => {
    const { file, getParams, operationId } = options;

    if (file.uploaded) return options;

    const newOptions = { ...options, file: { ...file } };
    try {
      newOptions.response = await client.execute({
        operationId,
        parameters: getParams(obj),
      });
      newOptions.file.uploaded = true;
    } catch (e) {
      newOptions.file.error = true;
    }
    return newOptions;
  };

  // send request for each of new files
  const newFiles = await Promise.all(getUploads(formState).map(upload));

  // update form state with the status of uploading - true if all files are uploaded successfully
  const newFilesPatch = getStatePatch(newFiles, formState);
  const isSuccess = newFiles.every(isUploaded);

  callback(isSuccess, newFilesPatch);

  if (newFiles.some(isError)) {
    throwErrorMessage(t`Some of the files have failed to upload`);
  }

  return isSuccess;
};

export default makeSaveFilesForForm;
