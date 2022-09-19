import React from 'react';
import { FormFeedback } from 'reactstrap';

import has from 'lodash/has';
import get from 'lodash/get';
import snakeCase from 'lodash/snakeCase';
import { v4 as uuid } from 'uuid';

import { updateFileName } from '@utils/files';

export function addFieldRow({ key, defaultObject }) {
  const { form } = this.state;

  this.setState({
    form: {
      ...form,
      [key]: [...form[key], { localId: uuid(), ...defaultObject }],
    },
  });
}

export function removeFieldRow(event, key) {
  const {
    dataset: { id },
  } = event.currentTarget;

  const { form } = this.state;

  this.setState({
    form: {
      ...form,
      [key]: form[key].filter((item) => {
        if (item.id) return String(item.id) !== String(id);
        else if (item.localId) return item.localId !== String(id);
        return true;
      }),
    },
  });
}

export const getNewResumeRequests = ({ allResume, name, operationId }) => {
  const result = [];

  // add new resume (only those which have fileObject)
  allResume.forEach((resume) => {
    if (resume.fileObject) {
      // we need to change resume file name to custom name based on candidate name and resume type,
      // as File entity it read only, we create new File with same options but with new file name to do so
      const newResumeFile = new File(
        [resume.fileObject],
        updateFileName(resume.ftype, name, resume.fileObject.name),
        { type: resume.fileObject.type, lastModified: resume.fileObject.lastModified }
      );

      result.push({
        file: { fileObject: newResumeFile, ...resume },
        operationId,
        getParams: (candidate) => ({
          id: candidate.id,
          ftype: snakeCase(resume.ftype),
          file: newResumeFile,
        }),
        ftype: resume.ftype,
        isResume: true,
      });
    }
  });

  return result;
};

export const processListUpload = (upload, files, newFiles) => {
  if (upload.response) {
    files.push(upload.response.obj);
  } else {
    newFiles.push(upload.file);
  }
};

export const getErrorsInputFeedback = (errors, field) => {
  if (!has(errors, field)) return null;

  return get(errors, field)?.map?.((e, i) => (
    <FormFeedback key={i} className='force-feedback'>
      {e}
    </FormFeedback>
  ));
};

export const getErrorsInputInvalid = (errors, field) => {
  return has(errors, field) ? true : undefined;
};

export const formatSubfield = (baseField, field) =>
  baseField ? `${baseField}.${field}` : field;
