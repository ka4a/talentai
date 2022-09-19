import React, { memo } from 'react';

import classnames from 'classnames';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { getFormattedDate } from '@utils';
import { LabeledItem, FormSection } from '@components';

import styles from './JobDetailsSections.module.scss';

const Metadata = ({ job }) => {
  return (
    <FormSection id='job-metadata' titleVariant='subheading' title={t`Metadata`}>
      <div className={classnames([styles.rowWrapper, styles.twoElements])}>
        <LabeledItem label={t`Date Opened`} value={getFormattedDate(job.publishedAt)} />
        <LabeledItem label={t`Date Closed`} value={getFormattedDate(job.closedAt)} />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.twoElements, styles.topGap])}
      >
        <LabeledItem
          label={t`Created By`}
          value={
            job?.createdBy && `${job?.createdBy.firstName} ${job.createdBy.lastName}`
          }
          isDisabled={true}
        />
        <LabeledItem label={t`ID`} value={job.id} />
      </div>

      <div
        className={classnames([styles.rowWrapper, styles.twoElements, styles.topGap])}
      >
        <LabeledItem
          label={t`Created Date`}
          value={getFormattedDate(job.publishedAt)}
        />
        <LabeledItem label={t`Modified Date`} value={getFormattedDate(job.updatedAt)} />
      </div>
    </FormSection>
  );
};

Metadata.propTypes = {
  job: PropTypes.object.isRequired,
};

export default memo(Metadata);
