import { client } from '@client';

export default function updateInterview(id, data) {
  return client.execute({
    operationId: 'proposal_interviews_partial_update',
    parameters: {
      id,
      data,
    },
  });
}
