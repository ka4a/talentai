import React from 'react';
import { Button, FormGroup, Label } from 'reactstrap';
import { Link } from 'react-router-dom';

import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { getErrorsInputFeedback } from '@utils';

import SwaggerForm from '../SwaggerForm';
import LocaleOptionsProvider from '../../components/LocaleOptionsProvider';

class SignUpRecruiterForm extends React.Component {
  getInputs = ({ FormInput, errors }) => (
    <div className='mb-16'>
      <FormGroup>
        <FormInput name='firstName' label={this.props.i18n._(t`First Name`)} required />
      </FormGroup>

      <FormGroup>
        <FormInput name='lastName' label={this.props.i18n._(t`Last Name`)} required />
      </FormGroup>
      <FormGroup>
        <LocaleOptionsProvider
          optionsKey='countries'
          render={(options) => (
            <FormInput
              searchable
              type='select'
              name='country'
              label={<Trans>Country</Trans>}
              options={options}
              getValue={(option) => option.code}
            />
          )}
        />
      </FormGroup>
      <FormGroup>
        <Label name='user.email'>
          <Trans>Email Address</Trans>
        </Label>
        <FormInput type='email' name='email' disabled />
      </FormGroup>

      <FormGroup>
        <FormInput
          type='password'
          name='password'
          label={this.props.i18n._(t`Password`)}
          required
        />
      </FormGroup>

      <FormGroup check>
        <Label check>
          <FormInput
            type='checkbox'
            name='termsOfService'
            required
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
    const { viaJob, email, onSaved } = this.props;

    return (
      <SwaggerForm
        formId='clientRegistrationRequestForm'
        operationId='recruiter_sign_up_register'
        onSaved={onSaved}
        initialState={{
          viaJob,
          email,
          firstName: '',
          lastName: '',
          password: '',
          termsOfService: false,
        }}
        inputs={this.getInputs}
        buttons={this.getButtons}
      />
    );
  }
}

SignUpRecruiterForm.propTypes = {
  email: PropTypes.string.isRequired,
  viaJob: PropTypes.string,
  onSaved: PropTypes.func,
};

export default withI18n()(SignUpRecruiterForm);
