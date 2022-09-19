import { useCallback, useState, useRef, useEffect } from 'react';

import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';

import { client as originalClient } from '@client';
import { checkZohoDuplication, getOriginalCandidate } from '@utils';

const DUMMY_INPUT = { value: '' };

const client = {
  abort() {},
  execute(args) {
    return new Promise((resolve, reject) => {
      client.abort = reject;
      originalClient.execute(args).then(resolve, reject);
    });
  },
};

const handleCancel = () => {
  client.abort();
};

function ZohoImport(props) {
  const { onSuccess, children, onError } = props;
  const inputRef = useRef(DUMMY_INPUT);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(
    () => () => {
      handleCancel();
    },
    [] // eslint-disable-line
  );

  const handleConfirm = useCallback(async () => {
    setIsLoading(true);
    try {
      const { obj } = await client.execute({
        operationId: 'zoho_get_candidate',
        parameters: {
          data: {
            url: inputRef.current.value,
          },
        },
      });
      let candidateId = null;
      let original = null;

      const analysis = (await checkZohoDuplication(obj)) || {};

      if (analysis.shouldBeRestored) {
        const response = await client.execute({
          operationId: 'candidate_restore',
          parameters: { id: analysis.toRestore[0].id, data: {} },
        });
        candidateId = response.obj.id;
      } else if (analysis.shouldFlagDuplication) {
        original = getOriginalCandidate(analysis);
      }

      if (candidateId == null) {
        const response = await client.execute({
          operationId: 'zoho_save_candidate',
          parameters: {
            data: { ...obj, original },
          },
        });
        candidateId = response.obj.id;
      }

      onSuccess(candidateId);
    } catch (error) {
      onError(error);
    } finally {
      setIsLoading(false);
    }
  }, [setIsLoading, onSuccess, onError]);

  return children({
    name: 'zohoUrl',
    inputRef,
    onConfirm: handleConfirm,
    onCancel: handleCancel,
    isLoading,
  });
}

ZohoImport.propTypes = {
  jobId: PropTypes.number,
  stage: PropTypes.string,
  children: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
};

ZohoImport.defaultProps = {
  stage: null,
  onSuccess() {},
};

export default withI18n()(ZohoImport);
