import React from 'react';

import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import ModalForm from '@components/modals/ModalForm';
import ForeignKeyInput from '@components/jobs/ForeignKeyInput';

class MoveProposalModalForm extends React.Component {
  getInputs = ({ form, errors, setValue }) => (
    <div>
      <ForeignKeyInput
        title={this.props.i18n._(t`Job`)}
        operationId='jobs_list'
        params={{
          check_candidate_proposed: form.candidate.id,
          check_user_has_access: form.createdBy.id,
          client: form.job.client,
          status: 'open',
        }}
        getOptionSelectedNameFn={(option) => <>{option.title}</>}
        getOptionNameFn={(option) => (
          <>
            {option.title}
            {option.candidateProposed ? (
              <span className='text-warning'>
                <Trans>
                  <span>&nbsp;</span>(already proposed)
                </Trans>
              </span>
            ) : null}
            {option.userHasAccess === false ? (
              <span className='text-warning'>
                <Trans>
                  <span>&nbsp;</span>(Recruiter has no access)
                </Trans>
              </span>
            ) : null}
          </>
        )}
        value={form.job}
        errors={errors.job}
        onChange={(value) => setValue('job', value)}
      />
    </div>
  );

  render() {
    const { proposalId, onSaved, onClosed } = this.props;

    return (
      <ModalForm
        formId='moveProposalModalForm'
        title={this.props.i18n._(t`Reallocate Proposal`)}
        readOperationId='proposals_read'
        operationId='proposals_move_to_job'
        processFormState={function (form) {
          return {
            id: form.id,
            job: form.job.id,
          };
        }}
        initialState={{ job: null }}
        editingId={proposalId}
        onSaved={onSaved}
        onClosed={onClosed}
        inputs={this.getInputs}
      />
    );
  }
}

MoveProposalModalForm.propTypes = {
  proposalId: PropTypes.any.isRequired,
  onSaved: PropTypes.func,
  onClosed: PropTypes.func,
};

export default withI18n()(MoveProposalModalForm);
