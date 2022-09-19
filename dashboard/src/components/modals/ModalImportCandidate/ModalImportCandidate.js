import React, { cloneElement, useCallback } from 'react';
import { Modal, ModalHeader, ModalBody } from 'reactstrap';
import { useToggle } from 'react-use';

import PropTypes from 'prop-types';
import _ from 'lodash';
import { Trans, t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import { showErrorToast } from '@utils';

import Typography from '../../UI/Typography';
import FormImportCandidate from '../../candidates/FormImportCandidate';

const UNIQUE_CANDIDATE_FIELD = ['zohoId', 'linkedinUrl', 'email', 'secondaryEmail'];

function ModalImportCandidate(props) {
  const { jobId, children, showTrigger, onSuccess, i18n, stage, onClosed } = props;

  const [isOpen, toggle] = useToggle(false);

  const handleSuccess = useCallback(
    (candidateId) => {
      onSuccess(candidateId);
      toggle(false);
    },
    [toggle, onSuccess]
  );

  const handleError = (error) => {
    let message = _.get(error, 'response.body.url'); // Invalid URL error
    if (!message) message = _.get(error, 'response.body.nonFieldErrors[0]');

    const errorKeys = _.keysIn(_.get(error, 'response.body', {}));
    if (_.intersection(errorKeys, UNIQUE_CANDIDATE_FIELD).length) {
      message = i18n._(t`Import failed. This candidate already exists in your DB`);
    }

    if (!message) message = _.get(error, 'message', null);

    if (message) {
      if (_.isArray(message)) {
        showErrorToast(
          <div>
            {_.map(message, (err) => (
              <div key={err}>{err}</div>
            ))}
          </div>
        );
      } else {
        showErrorToast(message);
      }
    }

    return message;
  };

  return (
    <>
      {showTrigger && cloneElement(children, { onClick: toggle })}

      <Modal isOpen={isOpen} size='lg'>
        <ModalHeader toggle={toggle}>
          <Typography variant='h3'>
            <Trans>Import candidate</Trans>
          </Typography>
        </ModalHeader>

        <ModalBody>
          <FormImportCandidate
            jobId={jobId}
            onSuccess={handleSuccess}
            onError={handleError}
            stage={stage}
            onClosed={onClosed}
          />
        </ModalBody>
      </Modal>
    </>
  );
}

ModalImportCandidate.propTypes = {
  showTrigger: PropTypes.bool,
  children: PropTypes.node.isRequired,
  onSuccess: PropTypes.func.isRequired,
  jobId: PropTypes.number,
  stage: PropTypes.string,
  onClosed: PropTypes.func,
};

ModalImportCandidate.defaultProps = {
  showTrigger: true,
  onSuccess() {},
  onClosed() {},
};

export default withI18n()(ModalImportCandidate);
