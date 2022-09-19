import React from 'react';
import { Button, Modal, ModalBody, ModalFooter, ModalHeader } from 'reactstrap';

import PropTypes from 'prop-types';
import _ from 'lodash';
import { Trans } from '@lingui/macro';

import SwaggerForm from '../SwaggerForm';
import Typography from '../UI/Typography/Typography';

function modalInputs(inputsFn, ...args) {
  return <ModalBody>{inputsFn(...args)}</ModalBody>;
}

function modalButtons(buttonsFn, ...args) {
  return <ModalFooter>{buttonsFn(...args)}</ModalFooter>;
}

export default class ModalForm extends React.PureComponent {
  state = {
    modal: true,
  };

  onSaved = (...args) => {
    this.setState({ modal: !this.props.closeOnSaved }, () => {
      if (this.props.onSaved) {
        this.props.onSaved(...args);
      }
    });
  };

  toggle = () => this.setState({ modal: !this.state.modal });
  onClosed = () => {
    // TODO: hack to avoid bug
    // https://github.com/reactstrap/reactstrap/issues/1279
    this.setState({ modal: false }, () => {
      this.props.onClosed();
    });
  };

  render() {
    const { title, inputs, buttons } = this.props;
    const { modal } = this.state;

    return (
      <Modal isOpen={modal} onClosed={this.onClosed} toggle={this.toggle} size='lg'>
        <ModalHeader toggle={this.toggle}>
          <Typography variant='h3'>{title}</Typography>
        </ModalHeader>

        <SwaggerForm
          formId={this.props.formId}
          readOperationId={this.props.readOperationId}
          operationId={this.props.operationId}
          processReadObject={this.props.processReadObject}
          processFormState={this.props.processFormState}
          processFormFiles={this.props.processFormFiles}
          editing={this.props.editingId}
          onSaved={this.onSaved}
          resetAfterSave={this.props.resetAfterSave}
          handlers={this.props.handlers}
          initialState={this.props.initialState}
          inputs={_.partial(modalInputs, inputs)}
          buttons={_.partial(modalButtons, buttons)}
        />
      </Modal>
    );
  }
}

ModalForm.propTypes = {
  formId: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,

  readOperationId: PropTypes.string,
  operationId: PropTypes.string,

  processReadObject: PropTypes.func,
  processFormState: PropTypes.func,
  processFormFiles: PropTypes.func,

  editingId: PropTypes.any,
  onSaved: PropTypes.func,
  onClosed: PropTypes.func,

  closeOnSaved: PropTypes.bool,

  handlers: PropTypes.object,

  initialState: PropTypes.object,
  inputs: PropTypes.func.isRequired,
  buttons: PropTypes.func,
};

ModalForm.defaultProps = {
  processReadObject: null,
  processFormState: null,

  editingId: null,
  handlers: {},
  onSaved: () => {},
  onClosed: () => {},
  closeOnSaved: true,
  // eslint-disable-next-line react/display-name
  buttons: (form, makeOnSubmit, defaultButtonAttrs) => (
    <Button {...defaultButtonAttrs}>
      <Trans>Save</Trans>
    </Button>
  ),
};
