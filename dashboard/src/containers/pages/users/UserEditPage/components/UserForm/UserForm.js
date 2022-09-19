import React, { useContext, useMemo } from 'react';
import { Form, Label } from 'reactstrap';
import { useSelector } from 'react-redux';
import { useHistory } from 'react-router';

import { t, Trans } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { FormContext } from '@contexts';
import {
  FormSection,
  BlockingPromptFormChanged,
  FormContextField,
  FormTitleHeader,
  DetailsGrid,
  LabeledItem,
  FormSubsection,
  Typography,
  ButtonBar,
  FormContextImageCropField,
} from '@components';
import { LOCALE_CHOICES, ROLE_CHOICES } from '@constants';
import { getFormattedDate } from '@utils';
import { useAsyncCallbackWithStatus, useTranslatedChoices } from '@hooks';

function UserForm(props) {
  const { isCreate } = props;

  const { onSubmit, initialForm, form } = useContext(FormContext);
  const history = useHistory();

  const [isSubmitting, handleSubmit] = useAsyncCallbackWithStatus(onSubmit);

  const { i18n } = useLingui();

  const languageOptions = useLanguageOptions(i18n);

  const countryOptions = useCountryOptions();

  const roleOptions = useRoleOptions(i18n);

  return (
    <Form onSubmit={handleSubmit}>
      <BlockingPromptFormChanged
        form={form}
        initialForm={initialForm}
        fieldsToSkip={FIELDS_SKIPPED_IN_CHANGE_CHECK}
      />
      <FormTitleHeader>
        <Trans>Edit User Details</Trans>
      </FormTitleHeader>
      <FormSection title={t`Details`}>
        <FormSubsection isGrid>
          <FormContextField label={t`First Name`} name='firstName' required />
          <FormContextField label={t`Last Name(s)`} name='lastName' required />
          <FormContextField
            label={t`Language`}
            name='locale'
            type='select'
            options={languageOptions}
          />
          <FormContextField
            label={t`Country`}
            name='country'
            type='select'
            options={countryOptions}
          />
          <FormContextField
            label={t`Email`}
            name='email'
            required
            disabled={!isCreate}
          />
        </FormSubsection>

        <FormSubsection>
          <Label for='photo'>
            <Typography variant='subheading'>Photo</Typography>
          </Label>

          <FormContextImageCropField
            deleteOperationId='staff_photo_delete'
            downloadOperationId='staff_photo_read'
            ftype='photo'
            fileKey='photo'
            newFileKey='newPhoto'
            withoutTitle
          />
        </FormSubsection>

        <FormSubsection isGrid>
          <FormContextField
            label={t`Role`}
            name='group'
            type='select'
            options={roleOptions}
            disabled
          />

          <div className='d-flex align-items-center'>
            <FormContextField
              label={t`Active`}
              name='isActive'
              type='checkbox'
              disabled
            />
          </div>
        </FormSubsection>
      </FormSection>

      <FormSection title={t`Metadata`} isLast>
        <DetailsGrid columnCount={4}>
          <LabeledItem label={t`ID`} value={form.id} />
          <LabeledItem label={t`Last Login`} value={getFormattedDate(form.lastLogin)} />
          <LabeledItem
            label={t`Created Date`}
            value={getFormattedDate(form.dateJoined)}
          />
        </DetailsGrid>
      </FormSection>
      <ButtonBar
        onCancel={history.goBack}
        onSave={handleSubmit}
        isDisabled={isSubmitting}
      />
    </Form>
  );
}

const FIELDS_SKIPPED_IN_CHANGE_CHECK = ['photo', 'newPhoto'];

function useLanguageOptions(i18n) {
  return useMemo(
    () =>
      LOCALE_CHOICES.map(({ value, transKey }) => ({ value, name: i18n._(transKey) })),
    [i18n]
  );
}

function useRoleOptions(i18n) {
  const orgType = useSelector(({ user }) => user.profile.org.type);

  return useTranslatedChoices(i18n, ROLE_CHOICES[orgType] ?? []);
}

function useCountryOptions() {
  const countries = useSelector(({ settings }) => settings.localeData.countries);

  return useMemo(
    () => countries.map((country) => ({ value: country.code, name: country.name })),
    [countries]
  );
}

UserForm.propTypes = {};

export default UserForm;
