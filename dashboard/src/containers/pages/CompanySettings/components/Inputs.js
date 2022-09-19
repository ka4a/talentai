import React from 'react';
import { useSelector } from 'react-redux';

import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';

import { FileInput, FormSection, Typography } from '@components';

import CareerPanel from './CareerPanel';

import styles from '../CompanySettings.module.scss';

const Inputs = ({ FormInput, form, setValue }) => {
  const countries = useSelector((state) => state.settings.localeData.countries);
  const functions = useSelector((state) => state.settings.localeData.functions);

  return (
    <FormSection>
      <div className={classnames([styles.rowWrapper, styles.twoElements])}>
        <FormInput name='name' label={t`Company Name (English)`} required />
        <FormInput name='nameJa' label={t`Company Name (Japanese)`} required />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.twoElements])}
      >
        <FormInput name='website' label={t`Website`} />

        <FormInput
          type='select'
          name='country'
          label={t`Country`}
          options={countries}
          valueKey='code'
          searchable
          required
        />
      </div>

      <div className={styles.topGap}>
        <FormInput
          type='multi-select'
          name='functionFocus'
          label={t`Function Focus`}
          options={functions}
          labelKey='label'
          required
        />
      </div>

      <hr />

      <Typography variant='subheading'>
        <Trans>Logo</Trans>
      </Typography>

      <div className={styles.topGap}>
        <FileInput
          deleteOperationId='client_settings_delete_logo'
          readOperationId='client_settings_download_logo'
          form={form}
          setValue={setValue}
          ftype='photo'
          filesKey='logo'
          newFilesKey='newLogo'
          acceptedFileType='image'
          withoutTitle
          limit={1}
        />
      </div>

      <hr />

      <CareerPanel FormInput={FormInput} setValue={setValue} form={form} />
    </FormSection>
  );
};

Inputs.propTypes = {
  FormInput: PropTypes.func.isRequired,
  setValue: PropTypes.func.isRequired,
  form: PropTypes.shape({}).isRequired,
};

export default Inputs;
