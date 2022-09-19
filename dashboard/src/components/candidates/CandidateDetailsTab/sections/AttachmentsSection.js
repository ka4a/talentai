import React, { memo } from 'react';

import { Trans } from '@lingui/macro';

import Typography from '@components/UI/Typography';

import AttachmentsList from './AttachmentsList';

import styles from '../CandidateDetailsSection.module.scss';

const AttachmentsSection = () => (
  <div className={styles.wrapper}>
    <Typography className={styles.title} variant={'subheading'}>
      <Trans>Attachments</Trans>
    </Typography>

    <AttachmentsList />
  </div>
);

export default memo(AttachmentsSection);
