import React, { useCallback, useMemo } from 'react';
import { Row, Button, FormGroup } from 'reactstrap';
import { Link } from 'react-router-dom';

import _ from 'lodash';
import { Trans } from '@lingui/macro';

import { FormSectionOld } from '@components/FormSectionOld';

import SwaggerForm from '../../../../components/SwaggerForm';
import UserOptionsProvider from '../../../../components/UserOptionsProvider';
import UserActionDateInfo from '../../../../components/UserActionDateInfo';
import LocaleOptionsProvider from '../../../../components/LocaleOptionsProvider';

export default function AgencyClientEditForm(props) {
  const { editingId, onSaved } = props;

  const initialState = useMemo(
    () => ({
      id: editingId,
      accountManager: null,
      originator: null,
      info: '',
      notes: '',
      type: '',
      industry: '',
      billingAddress: '',
      portalUrl: '',
      portalLogin: '',
      portalPassword: '',
      primaryContactNumber: '',
      website: '',
    }),
    [editingId]
  );

  const processFormState = useCallback((form) => {
    let number = form.primaryContactNumber;

    if (number && !_.startsWith(number, '+')) {
      number = '+' + number;
    }
    return { ...form, primaryContactNumber: number };
  }, []);

  const getInputs = useCallback(({ form, FormInputBlock, FormInput }) => {
    return (
      <>
        <FormSectionOld>
          <Trans>General info</Trans>
        </FormSectionOld>
        <Row>
          <UserOptionsProvider>
            <FormInputBlock
              type='select'
              searchable
              name='accountManager'
              label={<Trans>Account Manager</Trans>}
            />
          </UserOptionsProvider>
          <UserOptionsProvider>
            <FormInputBlock
              type='select'
              searchable
              label={<Trans>Originator</Trans>}
              name='originator'
            />
          </UserOptionsProvider>
        </Row>
        <FormGroup>
          <FormInput
            type='rich-editor'
            name='info'
            label={<Trans>Client Info</Trans>}
          />
        </FormGroup>
        <FormGroup>
          <FormInput type='rich-editor' name='notes' label={<Trans>Notes</Trans>} />
        </FormGroup>

        <hr className='mt-24' />
        <FormSectionOld>
          <Trans>Company Information</Trans>
        </FormSectionOld>
        <Row>
          <LocaleOptionsProvider
            optionsKey='clientTypes'
            render={(options) => (
              <FormInputBlock
                type='select'
                searchable
                name='type'
                label={<Trans>Type</Trans>}
                options={options}
              />
            )}
          />
          <LocaleOptionsProvider
            optionsKey='industries'
            render={(options) => (
              <FormInputBlock
                type='select'
                searchable
                name='industry'
                label={<Trans>Industry</Trans>}
                options={options}
              />
            )}
          />
          <FormInputBlock
            name='primaryContactNumber'
            label={<Trans>Primary Contact Number</Trans>}
          />
          <FormInputBlock
            name='billingAddress'
            label={<Trans>Billing Address</Trans>}
          />
          <FormInputBlock
            type='url'
            name='website'
            placeholder='https://'
            label={<Trans>Website</Trans>}
          />
        </Row>

        <hr className='mt-24' />
        <FormSectionOld>
          <Trans>Portal Information</Trans>
        </FormSectionOld>
        <Row>
          <FormInputBlock
            type='url'
            name='portalUrl'
            placeholder='https://'
            label={<Trans>Portal URL</Trans>}
          />
          <FormInputBlock name='portalLogin' label={<Trans>Portal Login</Trans>} />
          <FormInputBlock
            type='password'
            name='portalPassword'
            label={<Trans>Portal Password</Trans>}
          />
        </Row>

        <hr className='mt-24' />
        <FormSectionOld>
          <Trans>Other Info</Trans>
        </FormSectionOld>
        <LocaleOptionsProvider
          optionsKey='invoiceOn'
          render={(options) => (
            <FormInputBlock
              label={<Trans>IOS/IOA</Trans>}
              name='iosIoa'
              type='select'
              options={options}
            />
          )}
        />
        <UserActionDateInfo
          label={<Trans>Updated by</Trans>}
          date={form.updatedAt}
          user={form.updatedBy}
        />
        <div className='mb-48' />
      </>
    );
  }, []);

  const getButtons = useCallback(
    (form, makeOnSubmit, defaultButtonAttrs, atBottom) => {
      return (
        <div className='d-flex'>
          <div>
            {atBottom && editingId ? (
              <Link to='/a/clients/'>
                <Button type='button' className='btn-inv-primary pl-0'>
                  <Trans>Back to Client list</Trans>
                </Button>
              </Link>
            ) : null}
          </div>
          <div className='ml-auto'>
            {atBottom && editingId ? (
              <Button {...defaultButtonAttrs} onClick={makeOnSubmit()}>
                <Trans>Save</Trans>
              </Button>
            ) : null}
          </div>
        </div>
      );
    },
    [editingId]
  );

  return (
    <SwaggerForm
      formId='agencyClientEditForm'
      readOperationId='agency_client_info_read'
      operationId='agency_client_info_partial_update'
      editing={editingId}
      onSaved={onSaved}
      inputs={getInputs}
      buttons={getButtons}
      lookupField='client'
      initialState={initialState}
      processFormState={processFormState}
    />
  );
}
