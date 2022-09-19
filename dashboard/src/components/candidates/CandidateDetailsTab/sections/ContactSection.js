import React, { memo } from 'react';

import classnames from 'classnames';
import { Trans, t } from '@lingui/macro';

import LabeledItem from '@components/UI/LabeledItem';
import Typography from '@components/UI/Typography';
import { ShowAuthenticated } from '@components/auth';
import useGetCandidate from '@swrAPI/hooks/candidates/useGetCandidate';

import { ROLES_WITH_FULL_CANDIDATE_ACCESS } from '../constants';

import styles from '../CandidateDetailsSection.module.scss';

const ContactSection = () => {
  const { data: candidate } = useGetCandidate();

  return (
    <div className={styles.wrapper}>
      <Typography variant='subheading' className={styles.title}>
        <Trans>Contact</Trans>
      </Typography>

      <ShowAuthenticated groups={ROLES_WITH_FULL_CANDIDATE_ACCESS}>
        <div className={classnames(styles.row, styles.mb20)}>
          <LabeledItem
            label={t`Email (Primary)`}
            value={candidate.email}
            withCapitalize={false}
          />
          <LabeledItem
            label={t`Email (Secondary)`}
            value={candidate.secondaryEmail}
            withCapitalize={false}
          />
        </div>

        <div className={classnames(styles.row, styles.withBorder)}>
          <LabeledItem label={t`Phone Number (Primary)`} value={candidate.phone} />
          <LabeledItem
            label={t`Phone Number (Secondary)`}
            value={candidate.secondaryPhone}
          />
        </div>

        <div className={classnames(styles.row, styles.withBorder)}>
          <LabeledItem
            label={t`Address`}
            value={candidate.address}
            withCapitalize={false}
          />
        </div>
      </ShowAuthenticated>
      <div className={classnames(styles.row)}>
        <LabeledItem
          label={t`Linkedin Profile`}
          value={candidate.linkedinUrl}
          withCapitalize={false}
          isLink
        />
      </div>
    </div>
  );
};

export default memo(ContactSection);
