import { useCallback } from 'react';

import { client } from '@client';
import { fetchErrorHandler } from '@utils';

export default function useHandleSwitchEnabled(options) {
  const {
    updateOperationId,
    createOperationId,
    openConfirmDisableDialog,
    isEnabled,
    mutate,
    isPostingExists,
    job,
  } = options;

  async function handleSwitchEnabled(shouldBeEnabled) {
    if (isEnabled && !shouldBeEnabled) {
      try {
        await openConfirmDisableDialog();
      } catch (error) {
        return;
      }
    }
    try {
      const response = isPostingExists
        ? await setPostingEnabled(updateOperationId, job.id, shouldBeEnabled)
        : await createPosting(createOperationId, job);
      if (mutate && response?.obj) await mutate(response.obj);
    } catch (error) {
      fetchErrorHandler(error);
    }
  }

  return useCallback(handleSwitchEnabled, [
    job,
    isPostingExists,
    isEnabled,
    mutate,
    updateOperationId,
    createOperationId,
    openConfirmDisableDialog,
  ]);
}

const createPosting = (operationId, job, isEnabled = true) => {
  const params = {
    ...job,
    isEnabled,
    jobId: job.id,
    function: job.function?.id || null,
  };
  return client.execute({
    operationId,
    parameters: {
      data: params,
    },
  });
};

const setPostingEnabled = (operationId, jobId, isEnabled) =>
  client.execute({
    operationId,
    parameters: {
      job_id: jobId,
      data: { isEnabled },
    },
  });
