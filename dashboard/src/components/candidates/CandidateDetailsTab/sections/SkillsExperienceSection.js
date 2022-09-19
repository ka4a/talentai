import React, { memo } from 'react';

import classnames from 'classnames';
import { Trans, t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { getChoiceName } from '@utils';
import { CERTIFICATION_CHOICES } from '@constants';
import { Badge, DetailsSection, FormattedLanguage } from '@components';
import LabeledItem from '@components/UI/LabeledItem';
import Typography from '@components/UI/Typography';
import useGetCandidate from '@swrAPI/hooks/candidates/useGetCandidate';
import { useTranslatedChoices } from '@hooks';

import styles from '../CandidateDetailsSection.module.scss';

const SkillsExperienceSection = () => {
  const { i18n } = useLingui();
  const certificationChoices = useTranslatedChoices(i18n, CERTIFICATION_CHOICES);

  const { data: candidate } = useGetCandidate();
  return (
    <DetailsSection title={`Skills & Experience`}>
      {renderSkillContent(candidate, certificationChoices)}
      <div className={styles.row}>
        <LabeledItem
          label={t`Working Experience`}
          value={candidate.experienceDetails?.summary}
          variant='textarea'
        />

        <LabeledItem
          label={t`Maximum No. of People Managed`}
          value={candidate.maxNumPeopleManaged}
          variant='number'
        />
      </div>
    </DetailsSection>
  );
};

function renderSkillContent(candidate, certificationChoices) {
  const { languages = [], certifications = [] } = candidate;

  const skills = candidate.tags ?? [];

  const skillContent = [];

  if (skills.length > 0)
    skillContent.push(
      <div
        key='tags'
        className={classnames(styles.row, styles.withBorder, styles.skills)}
      >
        {skills.map((skill) => (
          <Badge key={skill.id} text={skill.name} />
        ))}
      </div>
    );

  if (languages.length > 0)
    skillContent.push(
      <div
        key='lang'
        className={classnames(styles.row, styles.withBorder, styles.countriesRow)}
      >
        {languages.map((language) => (
          <FormattedLanguage
            key={language.id}
            countryCode={language.language}
            langLabel={language.formatted.split(' ')[0]}
            level={language.level}
            type='withSubLevel'
          />
        ))}
      </div>
    );

  if (certifications.length > 0)
    skillContent.push(
      <div
        key='cert'
        className={classnames(styles.row, styles.withBorder, styles.countriesRow)}
      >
        {certifications.map((certification) => (
          <div key={certification.id}>
            <LabeledItem
              label={getCertificationLabel(certification, certificationChoices)}
              value={certification.score}
            />
          </div>
        ))}
      </div>
    );

  if (skillContent.length < 1) return null;

  return (
    <>
      <Typography variant='caption' className={styles.skillsTitle}>
        <Trans>Skills</Trans>
      </Typography>
      {skillContent}
    </>
  );
}

function getCertificationLabel({ certification, certificationOther }, choices) {
  if (certificationOther) return certificationOther;
  return getChoiceName(choices, certification);
}

export default memo(SkillsExperienceSection);
