import React from 'react';
import { Button, FormGroup, Label } from 'reactstrap';
import { Link } from 'react-router-dom';

import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { getErrorsInputFeedback } from '@utils';

import SwaggerForm from '../SwaggerForm';
import CountriesOptionsProvider from '../CountriesOptionsProvider';

class SignUpClientForm extends React.Component {
  getInputs = ({ FormInput, errors }) => (
    <div className='mb-16'>
      <FormGroup>
        <FormInput name='name' label='Client Name' required tabIndex='1' />
      </FormGroup>

      <FormGroup>
        <CountriesOptionsProvider>
          <FormInput
            searchable
            type='select'
            name='country'
            label={this.props.i18n._(t`Country`)}
            tabIndex='2'
          />
        </CountriesOptionsProvider>
      </FormGroup>

      <h3>
        <Trans>Primary Contact</Trans>
      </h3>

      <FormGroup>
        <FormInput
          name='user.firstName'
          label={this.props.i18n._(t`First Name`)}
          required
          tabIndex='3'
        />
      </FormGroup>

      <FormGroup>
        <FormInput
          name='user.lastName'
          label={this.props.i18n._(t`Last Name`)}
          required
          tabIndex='4'
        />
      </FormGroup>

      <FormGroup>
        <Label name='user.email'>
          <Trans>Email Address</Trans>
        </Label>
        <FormInput type='email' name='user.email' disabled />
      </FormGroup>

      <FormGroup>
        <FormInput
          type='password'
          name='user.password'
          label={this.props.i18n._(t`Password`)}
          required
          tabIndex='5'
        />
      </FormGroup>

      <FormGroup>
        <CountriesOptionsProvider>
          <FormInput
            searchable
            type='select'
            name='user.country'
            label={this.props.i18n._(t`Country`)}
            tabIndex='6'
          />
        </CountriesOptionsProvider>
      </FormGroup>

      <FormGroup check>
        <Label check>
          <FormInput
            type='checkbox'
            name='termsOfService'
            required
            tabIndex='7'
            renderErrors={false}
          />{' '}
          <Trans>
            I agree to <Link to='/legal/terms-of-service'>Terms Of Service</Link>
          </Trans>
          {getErrorsInputFeedback(errors, 'termsOfService')}
        </Label>
      </FormGroup>
    </div>
  );

  getButtons = (form, makeOnSubmit, defaultButtonAttrs) => (
    <div>
      <Button {...defaultButtonAttrs}>
        <Trans>Sign Up</Trans>
      </Button>
    </div>
  );

  render() {
    const { email, onSaved } = this.props;

    return (
      <SwaggerForm
        formId='clientRegistrationRequestForm'
        operationId='client_registration_request_create'
        onSaved={onSaved}
        initialState={{
          name: '',
          user: {
            email,
            firstName: '',
            lastName: '',
            password: '',
          },
          termsOfService: false,
        }}
        inputs={this.getInputs}
        buttons={this.getButtons}
      />
    );
  }
}

SignUpClientForm.propTypes = {
  email: PropTypes.string.isRequired,
  onSaved: PropTypes.func,
};

export default withI18n()(SignUpClientForm);
