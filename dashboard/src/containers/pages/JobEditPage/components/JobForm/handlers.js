import { t } from '@lingui/macro';

import { isDialogConfirmed, makeSaveFilesForForm, warningDialog } from '@utils';

import openConfirmCloseUnfilled from './utils/openConfirmCloseUnfilled';
import openCantBeFilled from './utils/openCantBeFilled';

export function setOpeningsCount({ target }) {
  this.setState(({ form }) => {
    const newForm = { ...form };
    newForm.openingsCount = target.value;
    if (form.hiredCount >= newForm.openingsCount) newForm.status = 'filled';
    return { form: newForm };
  });
}

// other handlers
export const processReadObject = (obj) => ({
  ...obj,
  managers: obj.managers?.[0]?.id ? [obj.managers?.[0]?.id] : [],
  interviewTemplates: obj.interviewTemplates.map((el) => ({
    ...el,
    interviewer: el.interviewer?.id ?? null,
  })),
  salaryFrom: obj.salaryFrom ?? '',
  salaryTo: obj.salaryTo ?? '',
  targetHiringDate: obj.targetHiringDate ?? '',
  probationPeriodMonths: obj.probationPeriodMonths ?? '',
  breakTimeMins: obj.breakTimeMins ?? '',
  paidLeaves: obj.paidLeaves ?? '',
  owner: obj.owner?.id ?? null,
  function: obj.function?.id ?? '',
  recruiters: obj.recruiters.map(({ id }) => ({ id, recruiter: id })),
});

export const getDisableReason = ({ form, userId, isAllowedToChangeStatus }) => {
  const reasonWhyDisabled = {
    status: null,
    openingsCount: null,
  };

  if (!(isAllowedToChangeStatus || form.owner === userId)) {
    reasonWhyDisabled.openingsCount = t`You have no permission to change number of openings`;

    if (form.status !== 'opened') {
      reasonWhyDisabled.status = t`You have no permission to open the job`;
    }
  } else {
    if (form.status === 'filled' && form.hiredCount >= form.openingsCount) {
      reasonWhyDisabled.status = t`
        To open a job you have to have more
        openings than number of hired candidates'
      `;
    }
  }

  return reasonWhyDisabled;
};

// form saving handlers
export const saveFiles = makeSaveFilesForForm(
  (state) =>
    state.newFiles.map((file) => ({
      file,
      operationId: 'job_files_create',
      getParams: ({ id }) => ({ job: id, file: file.file, title: file.title }),
    })),
  (newFiles) => ({
    newFiles: newFiles.map(({ file }) => file),
  })
);

export const updateFiles = makeSaveFilesForForm(
  (state) =>
    state.files.reduce((acc, file) => {
      if (file.changed) {
        acc.push({
          file,
          operationId: 'job_files_partial_update',
          getParams: () => ({ id: file.id, title: file.title }),
        });
      }

      return acc;
    }, []),
  (files) => ({
    files: files.map(({ file }) => file),
  })
);

export async function checkFormStateBeforeSave({ status, hiredCount, openingsCount }) {
  const availableOpenings = openingsCount - hiredCount;
  if (availableOpenings > 0) {
    switch (status) {
      case 'closed':
        return await isDialogConfirmed(openConfirmCloseUnfilled(availableOpenings));
      case 'filled':
        await warningDialog(openCantBeFilled(availableOpenings));
        return false;
      default:
        break;
    }
  }
  return true;
}
