import fileDownload from 'js-file-download';
import snakeCase from 'lodash/snakeCase';

import { client } from '@client';
import { fetchErrorHandler } from '@utils/errorHandling';

export const downloadFile = async (operationId, ftype = null, id) => {
  try {
    const { text, headers } = await client.execute({
      operationId,
      parameters: { id, ftype: snakeCase(ftype) },
    });

    fileDownload(text, headers['content-disposition'].split('"')[1]);
  } catch (error) {
    fetchErrorHandler(error);
  }
};

export const deleteFile = async (
  id,
  ftype = null,
  callback,
  operation = 'candidate_misc_file_delete'
) => {
  const operationId = ftype === null ? operation : 'candidates_delete_file';
  try {
    await client.execute({
      operationId,
      parameters: { id, ftype },
    });
    callback?.();
  } catch (err) {
    fetchErrorHandler(err);
  }
};

export const getFileName = (url) => {
  const cleanUrl = url.split('?', 1)[0];
  return cleanUrl.substring(cleanUrl.lastIndexOf('/') + 1);
};

export function withoutFileExtension(fileName) {
  const extStartIndex = fileName.lastIndexOf('.');
  if (extStartIndex === -1) return fileName;

  return fileName.substring(0, extStartIndex);
}

export function withNewExtension(fileName, extension) {
  return `${withoutFileExtension(fileName)}.${extension}`;
}

export const getFileExtension = (url) => {
  const filename = getFileName(url);
  const extStartIndex = filename.lastIndexOf('.');

  if (extStartIndex === -1) return '';

  return filename.substring(extStartIndex + 1).toLowerCase();
};

export const updateFileName = (resumeType, name, fileName) => {
  const updatedNames = {
    resume: `${name}_English_Resume.${getFileExtension(fileName)}`,
    resumeJa: `${name}_Japanese_Resume.${getFileExtension(fileName)}`,
    cvJa: `${name}_Japanese_CV.${getFileExtension(fileName)}`,
  };

  return updatedNames[resumeType] || fileName;
};

export const getFilePathWithoutParams = (path) => path.split('?', 1)[0];
