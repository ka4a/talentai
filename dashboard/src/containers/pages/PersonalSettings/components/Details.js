import React, { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { Label } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';

import { LOCALE_CHOICES } from '@constants';
import { FormImageCropInput, FormSection, Typography } from '@components';

import styles from '../PersonalSettings.module.scss';

const Details = ({ FormInput, setValue, form, errors }) => {
  const userGroups = useSelector((state) => state.user.groups);
  const countriesOptions = useSelector((state) => state.settings.localeData.countries);

  const roleOptions = useMemo(
    () =>
      userGroups.map((group) => ({
        name: group.substring(0, group.length - 1),
        value: group,
      })),
    [userGroups]
  );

  return (
    <FormSection id='settings-details' title={t`Details`}>
      <div className={classnames([styles.rowWrapper, styles.twoElements])}>
        <FormInput name='firstName' label={t`First Name`} required />
        <FormInput name='lastName' label={t`Last Name(s)`} required />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.twoElements])}
      >
        <FormInput
          type='select'
          name='locale'
          label={t`Language`}
          options={LOCALE_CHOICES}
          required
        />
        <FormInput
          type='select'
          name='country'
          label={t`Country`}
          options={countriesOptions}
          valueKey='code'
          searchable
        />
      </div>

      <div
        className={classnames([
          styles.rowWrapper,
          styles.topGap,
          styles.oneToTwoWrapper,
        ])}
      >
        <FormInput type='email' name='email' label={t`Email address`} required />
      </div>

      <div className={classnames(styles.attachments, styles.topGap)}>
        <Label for='photo'>
          <Typography variant='subheading'>Photo</Typography>
        </Label>

        <FormImageCropInput
          fileKey='photo'
          newFileKey='newPhoto'
          form={form}
          errors={errors}
          setValue={setValue}
          deleteOperationId='user_delete_photo'
          downloadOperationId='user_download_photo'
        />
      </div>

      <hr className='my-24' />

      <div
        className={classnames([styles.rowWrapper, styles.topGap, styles.twoElements])}
      >
        <FormInput
          searchable
          type='select'
          name='groups[0]'
          label={t`Role`}
          options={roleOptions}
          isDisabled
        />

        <div className={styles.roleCheckbox}>
          <FormInput
            searchable
            type='checkbox'
            name='isActive'
            label={t`Active`}
            isDisabled
          />
        </div>
      </div>
    </FormSection>
  );
};

Details.propTypes = {
  FormInput: PropTypes.func.isRequired,
  setValue: PropTypes.func.isRequired,
  form: PropTypes.shape({}).isRequired,
};

export default Details;
