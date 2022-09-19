import React from 'react';

import { t, Trans } from '@lingui/macro';

import { client } from '@client';
import Button from '@components/UI/Button';
import DuplicationMessage from '@components/modals/DuplicationMessage';
import { fetchErrorHandler } from '@utils/errorHandling';
import { openConfirm, openDialog } from '@utils/alert';

const getConfirmDuplicationCandidateButtons = (resolve, reject) => (
  <>
    <Button onClick={() => resolve(true)} variant='secondary' color='danger'>
      <Trans>Save anyway</Trans>
    </Button>

    <Button onClick={reject} variant='secondary' color='neutral'>
      <Trans>Cancel</Trans>
    </Button>

    <Button onClick={() => resolve(false)}>
      <Trans>Not a duplicate</Trans>
    </Button>
  </>
);

const getConfirmRestoreCandidateButtons = (resolve, reject) => (
  <>
    <Button onClick={() => resolve('RESTORE')} variant='secondary' color='danger'>
      <Trans>Restore</Trans>
    </Button>

    <Button onClick={reject} variant='secondary' color='neutral'>
      <Trans>Cancel</Trans>
    </Button>
  </>
);

const isOwnDuplicate = (obj) => obj != null && obj.duplicates.length > 0;
const hasAbsoluteMatch = (duplicates = []) => duplicates.some((e) => e.isAbsolute);

const genericDuplicationCheck = async (operationId, data) => {
  let response = null;

  try {
    response = await client.execute({ operationId, parameters: { data } });
  } catch (error) {
    // if we get validation error we will allow creation attempt
    // because it would fail and be handled by form correctly
    if (error.response && error.response.status === 400) return null;

    await openConfirm({
      title: t`Warning`,
      description: (
        <>
          <div>
            <Trans>Couldn&apos;t check if candidate is a duplicate</Trans>
          </div>
          <div>
            <Trans>Do you want to proceed anyway?</Trans>
          </div>
        </>
      ),
    });
  }

  const { obj } = response || {};

  if (!obj) return null;

  const { duplicates, lastSubmitted, toRestore, submittedByOthers } = obj;

  if (toRestore.length === 1) {
    obj.shouldBeRestored = await openDialog({
      title: t`Candidate duplication`,
      description: t`The candidate you are trying to import or create is a duplicate of a previously
        archived candidate. Do you want to restore the original candidate?`,
      getButtons: getConfirmRestoreCandidateButtons,
    });
  } else {
    if (hasAbsoluteMatch(duplicates)) return null;

    if (isOwnDuplicate(obj) || submittedByOthers) {
      obj.shouldFlagDuplication = await openDialog({
        title: t`Candidate duplication`,
        content: (
          <DuplicationMessage
            duplicates={duplicates}
            submittedByOthers={submittedByOthers}
            lastSubmitted={lastSubmitted}
          />
        ),
        getButtons: getConfirmDuplicationCandidateButtons,
      });
    } else {
      return null;
    }
  }
  return obj;
};

export const checkDuplication = (candidate) => {
  return genericDuplicationCheck('candidate_check_duplication', {
    id: candidate.id,
    firstName: candidate.firstName,
    lastName: candidate.lastName,
    firstNameKanji: candidate.firstNameKanji,
    lastNameKanji: candidate.lastNameKanji,
    email: candidate.email,
    secondaryEmail: candidate.secondaryEmail,
    linkedinUrl: candidate.linkedinUrl,
    job: candidate.jobId,
  });
};

export const checkLinkedInDuplication = (candidate) => {
  return genericDuplicationCheck(
    'candidate_linkedin_data_check_duplication',
    candidate
  );
};

export const checkZohoDuplication = (candidate) => {
  return genericDuplicationCheck('candidate_check_duplication', candidate);
};

export const getOriginalCandidate = (obj) => {
  if (isOwnDuplicate(obj)) return obj.duplicates[0].id;

  return null;
};

export const makeCheckForDuplicationBeforeSave = (getContext) => async (
  form,
  patchForm,
  resetFormState
) => {
  const { id, jobId, redirect } = getContext();

  try {
    const analysis = await checkDuplication({ ...form, id, jobId });

    if (analysis) {
      if (analysis.shouldBeRestored) {
        const archivedId = analysis.toRestore[0].id;

        try {
          await client.execute({
            operationId: 'candidate_restore',
            parameters: { id: archivedId, data: {} },
          });
          resetFormState(() => redirect(`/candidate/${archivedId}/edit`));
        } catch (error) {
          fetchErrorHandler(error);
        }

        return false;
      }

      patchForm({
        original: analysis.shouldFlagDuplication
          ? getOriginalCandidate(analysis)
          : null,
      });
    }
    return true;
  } catch (error) {
    return false;
  }
};
