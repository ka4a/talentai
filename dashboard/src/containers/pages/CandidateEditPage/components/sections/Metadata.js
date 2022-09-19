import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';

import { getFormattedDate } from '@utils';
import { FormSection, LabeledItem } from '@components';

import styles from '../CandidateForm/CandidateForm.module.scss';

const Metadata = ({ form }) => (
  <FormSection id='metadata-edit' title={t`Metadata`}>
    <div className={classnames([styles.rowWrapper, styles.twoElements])}>
      <LabeledItem
        label={t`Created By`}
        value={`${form.createdBy?.firstName ?? ''} ${form.createdBy?.lastName ?? ''}`}
      />
      <LabeledItem label={t`ID`} value={form.id} />
    </div>

    <div className={classnames([styles.rowWrapper, styles.twoElements, styles.topGap])}>
      <LabeledItem label={t`Created Date`} value={getFormattedDate(form.createdAt)} />
      <LabeledItem label={t`Modified Date`} value={getFormattedDate(form.updatedAt)} />
    </div>
  </FormSection>
);

Metadata.propTypes = {
  form: PropTypes.shape({
    id: PropTypes.number,
    createdBy: PropTypes.shape({
      firstName: PropTypes.string,
      lastName: PropTypes.string,
    }),
    createdAt: PropTypes.string,
    updatedAt: PropTypes.string,
  }).isRequired,
};

export default memo(Metadata);
