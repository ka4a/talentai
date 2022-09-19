import React from 'react';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import classnames from 'classnames';

import { getFormattedDate } from '@utils';
import { FormSection, LabeledItem } from '@components';

import styles from '../JobForm/JobForm.module.scss';

const Metadata = ({ FormInput, form }) => {
  return (
    <FormSection id='metadata-edit' title={t`Metadata`}>
      <div className={classnames([styles.rowWrapper, styles.twoElements])}>
        <FormInput type='simple-datepicker' name='publishedAt' label={t`Date Opened`} />
        <FormInput type='simple-datepicker' name='closedAt' label={t`Date Closed`} />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.twoElements, styles.topGap])}
      >
        <LabeledItem
          label={t`Created By`}
          value={
            form.createdBy && `${form.createdBy.firstName} ${form.createdBy.lastName}`
          }
        />
        <LabeledItem label={t`ID`} value={form.id} />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.twoElements, styles.topGap])}
      >
        <LabeledItem label={t`Created Date`} value={getFormattedDate(form.createdAt)} />
        <LabeledItem
          label={t`Modified Date`}
          value={getFormattedDate(form.updatedAt)}
        />
      </div>
    </FormSection>
  );
};

Metadata.propTypes = {
  FormInput: PropTypes.func.isRequired,
  form: PropTypes.shape({}).isRequired,
};

export default Metadata;
