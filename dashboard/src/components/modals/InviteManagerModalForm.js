import React from 'react';
import { FormGroup, Row, Col } from 'reactstrap';

import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import ModalForm from './ModalForm';

class InviteManagerModalForm extends React.Component {
  getInputs = ({ FormInput }) => (
    <div>
      <Row>
        <Col>
          <FormGroup>
            <FormInput name='firstName' label={this.props.i18n._(t`First Name`)} />
          </FormGroup>
        </Col>
        <Col>
          <FormGroup>
            <FormInput name='lastName' label={this.props.i18n._(t`Last Name`)} />
          </FormGroup>
        </Col>
      </Row>
      <FormGroup>
        <FormInput type='email' name='email' label={this.props.i18n._(t`Email`)} />
      </FormGroup>
    </div>
  );

  render() {
    const { onSaved, onClosed } = this.props;

    return (
      <ModalForm
        formId='managersInviteModalForm'
        title={this.props.i18n._(t`Invite a Manager`)}
        operationId='managers_invite'
        onSaved={onSaved}
        onClosed={onClosed}
        size='sm'
        initialState={{ firstName: '', lastName: '', email: '' }}
        inputs={this.getInputs}
      />
    );
  }
}

InviteManagerModalForm.propTypes = {
  editingId: PropTypes.any,
  onSaved: PropTypes.func,
  onClosed: PropTypes.func,
};

export default withI18n()(InviteManagerModalForm);
