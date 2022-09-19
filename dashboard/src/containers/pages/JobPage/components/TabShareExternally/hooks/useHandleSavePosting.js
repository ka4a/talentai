import { useCallback } from 'react';

import { fetchErrorHandler } from '@utils';
import { client } from '@client';

export default function useHandleSavePosting(options) {
  const { jobId, operationId, refresh, setIsModalOpen, isEnabled } = options;

  async function handleSavePosting(form) {
    try {
      const response = await submitForm(operationId, jobId, {
        isEnabled,
        ...form,
      });
      if (refresh && response?.obj) await refresh(response.obj);
    } catch (error) {
      fetchErrorHandler(error);
    }
    setIsModalOpen(false);
  }

  return useCallback(handleSavePosting, [
    operationId,
    jobId,
    refresh,
    setIsModalOpen,
    isEnabled,
  ]);
}

const submitForm = (operationId, jobId, form) =>
  client.execute({
    operationId,
    parameters: {
      job_id: jobId,
      data: form,
    },
  });
