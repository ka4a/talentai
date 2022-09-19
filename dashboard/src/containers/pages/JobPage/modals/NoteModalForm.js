import React from 'react';
import { FormGroup } from 'reactstrap';

import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { Trans } from '@lingui/macro';

import ModalForm from '@components/modals/ModalForm';

class NoteModalForm extends React.Component {
  getInputs = ({ FormInput }) => (
    <div>
      <FormGroup>
        <FormInput type='rich-editor' name={this.props.inputName} />
      </FormGroup>
    </div>
  );

  render() {
    const {
      readOperationId,
      operationId,
      inputName,
      editingId,
      title,
      onSaved,
      onClosed,
    } = this.props;
    return (
      <ModalForm
        formId='noteModalForm'
        title={title}
        readOperationId={readOperationId}
        operationId={operationId}
        processFormState={function (form) {
          return {
            id: form.id,
            [inputName]: form[inputName],
          };
        }}
        editingId={editingId}
        onSaved={onSaved}
        onClosed={onClosed}
        initialState={{ [inputName]: '' }}
        inputs={this.getInputs}
      />
    );
  }
}

NoteModalForm.propTypes = {
  readOperationId: PropTypes.string.isRequired,
  operationId: PropTypes.string.isRequired,
  inputName: PropTypes.string.isRequired,
  editingId: PropTypes.any.isRequired,
  title: PropTypes.string,
  onSaved: PropTypes.func,
  onClosed: PropTypes.func,
};

NoteModalForm.defaultProps = {
  title: <Trans>Note</Trans>,
};

export default withI18n()(NoteModalForm);
