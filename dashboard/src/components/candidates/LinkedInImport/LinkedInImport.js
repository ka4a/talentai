import { useState, useCallback, useRef, useEffect } from 'react';

import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import {
  checkLinkedInDuplication,
  checkIfProposedByLinkedin,
  getOriginalCandidate,
  retrieveLinkedInProfileData,
} from '@utils';
import { client } from '@client';

const EXTENSION_PROCESS_DUMMY = {
  isDummy: true,
  abort() {},
};

const REPLACEMENT_MESSAGES = {
  'Extension context invalidated.': t`Extension was updated. Please refresh the page to synchronise`,
};

const wrapper = withI18n();

const LinkedInImport = (props) => {
  const { onSuccess, children, jobId, i18n, onError } = props;
  const [isLoading, setIsLoading] = useState(false);
  const extensionProcess = useRef(EXTENSION_PROCESS_DUMMY);
  const inputRef = useRef({ value: '' });

  const handleCancel = useCallback(async () => {
    extensionProcess.current.abort();
    setIsLoading(false);
  }, [setIsLoading, extensionProcess]);

  // it cancels request if component is unmount
  useEffect(
    () => () => {
      handleCancel();
    },
    [] // eslint-disable-line
  );

  const handleConfirm = useCallback(async () => {
    // prevent starting another request if one is already running
    if (isLoading) return;
    const url = inputRef.current.value;

    setIsLoading(true);
    try {
      const shouldSkipDuplicationCheck = await checkIfProposedByLinkedin(url, jobId);
      // saving promise to be able to abort it if it hangs
      extensionProcess.current = retrieveLinkedInProfileData(url);

      const payload = await extensionProcess.current;
      let candidateId = null;
      let original = null;

      if (!shouldSkipDuplicationCheck) {
        let analysis = await checkLinkedInDuplication({
          ...payload,
          job: jobId,
        });
        analysis = analysis || {};

        if (analysis.shouldBeRestored) {
          const { obj: candidate } = await client.execute({
            operationId: 'candidate_restore',
            parameters: { id: analysis.toRestore[0].id, data: {} },
          });
          candidateId = candidate.id;
        } else if (analysis.shouldFlagDuplication) {
          original = getOriginalCandidate(analysis);
        }
      }

      if (candidateId == null) {
        const response = await client.execute({
          operationId: 'add_linkedin_candidate',
          parameters: {
            data: { ...payload, original },
          },
        });
        candidateId = response.obj.candidateId;
      }

      onSuccess(candidateId);
    } catch (error) {
      if (!onError(error)) {
        let message = error ? error.message : null;
        if (REPLACEMENT_MESSAGES[message]) {
          message = i18n._(REPLACEMENT_MESSAGES[message]);
        }
      }
    } finally {
      setIsLoading(false);
    }
  }, [jobId, isLoading, setIsLoading, extensionProcess, onSuccess, i18n, onError]);

  return children({
    name: 'linkedInUrl',
    inputRef,
    onConfirm: handleConfirm,
    onCancel: handleCancel,
    isLoading,
  });
};

LinkedInImport.propTypes = {
  children: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
  shouldCancel: PropTypes.func,
  ref: PropTypes.shape({
    current: PropTypes.shape({
      cancel: PropTypes.func,
    }),
  }),
  i18n: PropTypes.shape({
    _: PropTypes.func.isRequired,
  }).isRequired,
  jobId: PropTypes.number,
};

LinkedInImport.defaultProps = {
  stage: null,
  onSuccess() {},
  jobId: null,
};

export default wrapper(LinkedInImport);
