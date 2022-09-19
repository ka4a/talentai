import differenceBy from 'lodash/differenceBy';

import {
  clearNumberStr,
  getNewResumeRequests,
  makeSaveFilesForForm,
  processListUpload,
  replaceHttps,
} from '@utils';

import { SALARY_FIELDS } from './constants';

export const processFormState = (form) => {
  const newForm = {
    ...form,
    source: form.source ?? undefined,
    newPhoto: null,
    linkedinUrl: replaceHttps(form.linkedinUrl),
    birthdate: form.birthdate ?? null,
    maxNumPeopleManaged:
      form.maxNumPeopleManaged === '' ? null : form.maxNumPeopleManaged,
    experienceDetails: form.experienceDetails.map((el) => {
      if (el.currentlyPursuing) delete el.dateEnd;
      return el;
    }),
  };

  SALARY_FIELDS.forEach((key) => (newForm[key] = clearNumberStr(form[key])));

  return newForm;
};

export const saveFiles = makeSaveFilesForForm(
  (state) => {
    let files = [];

    const newResume = getNewResumeRequests({
      allResume: state.allResume,
      name: state.name,
      operationId: 'candidates_upload_file',
    });
    files = files.concat(newResume);

    // add new photo
    if (state.newPhoto) {
      files.push({
        file: state.newPhoto,
        operationId: 'candidates_upload_file',
        getParams: (candidate) => ({
          id: candidate.id,
          ftype: 'photo',
          file: state.newPhoto.file,
        }),
        isPhoto: true,
      });
    }

    // add all new other files
    state.newFiles.forEach((file) => {
      files.push({
        file,
        filesKey: 'files',
        newFilesKey: 'newFiles',
        operationId: 'candidate_misc_file_create',
        getParams: (candidate) => ({
          candidate: candidate.id,
          file: file.file,
          is_shared: file.isShared,
          title: file.title,
        }),
      });
    });

    return files;
  },
  (newFiles, state) => {
    const resumeFiles = newFiles.filter((el) => el.isResume);
    const oldResume = differenceBy(state.allResume, resumeFiles, 'ftype');

    return newFiles.reduce(
      (patch, upload) => {
        const { file, isPhoto, isResume } = upload;

        if (isPhoto) patch.newPhoto = file;
        else if (isResume) patch.allResume.push(file);
        else processListUpload(upload, patch.files, patch.newFiles);

        return patch;
      },
      { newFiles: [], files: [...state.files], allResume: [...oldResume] }
    );
  }
);

export const updateFiles = makeSaveFilesForForm(
  (state) =>
    state.files.reduce((acc, file) => {
      if (file.changed) {
        acc.push({
          file,
          operationId: 'candidate_misc_file_partial_update',
          getParams: () => ({ id: file.id, title: file.title }),
        });
      }

      return acc;
    }, []),
  (files) => ({
    files: files.map(({ file }) => file),
  })
);
