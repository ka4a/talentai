import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t, Trans } from '@lingui/macro';

import {
  Badge,
  FormattedLanguage,
  LabeledItem,
  Typography,
  FormSection,
} from '@components';

import styles from './JobDetailsSections.module.scss';

const Requirements = ({ job, privatePart }) => {
  return (
    <FormSection
      id='job-requirements'
      titleVariant='subheading'
      title={t`Requirements`}
    >
      <LabeledItem
        label={t`Requirements`}
        variant='textarea'
        value={job.requirements}
      />

      {privatePart}

      <Typography
        variant='caption'
        className={classnames([styles.skillTitle, styles.topGap])}
      >
        <Trans>Skills</Trans>
      </Typography>

      <div className={classnames([styles.skillsWrapper])}>
        {job.skills.map((skill, i) => (
          <Badge key={i} text={skill.name} className={styles.skillBadge} />
        ))}
      </div>

      <hr className={styles.topGap} />

      <Typography variant='subheading'>
        <Trans>Languages</Trans>
      </Typography>

      <div className={classnames(styles.languageWrapper)}>
        {job?.requiredLanguages?.map((lang) => (
          <FormattedLanguage
            key={lang.id}
            countryCode={lang.language}
            level={lang.level}
            type='withSubLevel'
          />
        ))}
      </div>
    </FormSection>
  );
};

Requirements.propTypes = {
  job: PropTypes.object.isRequired,
  privatePart: PropTypes.object.isRequired,
};

Requirements.defaultProps = {
  privatePart: null,
};

export default memo(Requirements);
