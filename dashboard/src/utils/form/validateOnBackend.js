import { client } from '@client';

async function validateOnBackend(operationId, partialForm, id) {
  try {
    await client.execute({ operationId, parameters: { id, data: partialForm } });
  } catch (error) {
    if (error?.response?.status === 400) {
      return error.response.obj;
    }
  }

  return {};
}

export default validateOnBackend;
