import React from 'react';
import { Button, ButtonGroup, FormGroup } from 'reactstrap';

import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import SwaggerForm from '../SwaggerForm';

function onSignUpTypeChangeHandler(value) {
  this.setState((state) => ({ form: { ...state.form, type: value } }));
}

class SignUpCheckEmailForm extends React.Component {
  getInputs = ({ FormInput, form, handlers }) => (
    <div className='mb-16'>
      <FormGroup>
        <FormInput
          type='email'
          name='email'
          label={this.props.i18n._(t`Email Address`)}
          required
        />
      </FormGroup>

      {this.props.type === null ? (
        <ButtonGroup>
          <Button
            type='button'
            color='primary'
            outline
            size='md'
            active={form.type === 'client'}
            onClick={() => handlers.onSignUpTypeChange('client')}
          >
            <Trans>Company</Trans>
          </Button>{' '}
          <Button
            type='button'
            color='primary'
            outline
            size='md'
            active={form.type === 'agency'}
            onClick={() => handlers.onSignUpTypeChange('agency')}
          >
            <Trans>Agency</Trans>
          </Button>
        </ButtonGroup>
      ) : null}
    </div>
  );

  getButtons = (form, makeOnSubmit, defaultButtonAttrs) => (
    <>
      <div className='clearfix'>
        <div className='float-right'>
          <Button {...defaultButtonAttrs}>
            <Trans>Continue</Trans>
          </Button>
        </div>
      </div>
    </>
  );

  render() {
    return (
      <SwaggerForm
        formId='recruiterSignUpForm'
        operationId='registration_check_email'
        onSaved={this.props.onChecked}
        handlers={{ onSignUpTypeChange: onSignUpTypeChangeHandler }}
        initialState={{
          type: this.props.type || 'client',
          email: '',
        }}
        inputs={this.getInputs}
        buttons={this.getButtons}
      />
    );
  }
}

SignUpCheckEmailForm.propTypes = {
  type: PropTypes.string,
  onChecked: PropTypes.func,
};

SignUpCheckEmailForm.defaultProps = {
  type: null,
};

export default withI18n()(SignUpCheckEmailForm);
