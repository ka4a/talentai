import { t } from '@lingui/macro';

import { client } from '@client';

async function checkIfProposedByLinkedin(linkedinUrl, job = null) {
  if (job === null) return false;

  const response = await client.execute({
    operationId: 'candidates_linkedin_url_check_proposed',
    parameters: { data: { linkedinUrl, job } },
  });

  const { isSubmitted, isExist } = response.obj;

  if (isSubmitted) {
    throw Error(t`This candidate has already been proposed for this job`);
  }

  return isExist;
}

export default checkIfProposedByLinkedin;
