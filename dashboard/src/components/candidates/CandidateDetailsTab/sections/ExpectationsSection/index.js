import React, { memo } from 'react';

import classnames from 'classnames';
import { Trans, t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { Typography, LabeledItem, ChoiceName } from '@components';
import { formatNumber, getChoiceName } from '@utils';
import {
  JOB_CHANGE_URGENCY_CHOICES,
  NOTICE_PERIOD_CHOICES,
  OTHER_DESIRED_BENEFIT_CHOICES,
} from '@constants';
import useGetCandidate from '@swrAPI/hooks/candidates/useGetCandidate';
import { useTranslatedChoices } from '@hooks';

import styles from '../../CandidateDetailsSection.module.scss';

const formatOtherBenefit = (details, choice) => `${choice}: ${details}`;

const ExpectationsSection = () => {
  const { i18n } = useLingui();
  const jobChangeUrgencyChoices = useTranslatedChoices(
    i18n,
    JOB_CHANGE_URGENCY_CHOICES
  );
  const noticePeriodChoices = useTranslatedChoices(i18n, NOTICE_PERIOD_CHOICES);
  const otherDesiredBenefitChoices = useTranslatedChoices(
    i18n,
    OTHER_DESIRED_BENEFIT_CHOICES
  );

  const { data: candidate } = useGetCandidate();

  return (
    <div className={styles.wrapper}>
      <div className='d-flex justify-content-between align-items-center'>
        <Typography variant='subheading'>
          <Trans>Candidate Expectations</Trans>
        </Typography>
      </div>

      <div className={classnames(styles.detailList, 'mt-3')}>
        <div className={styles.expectationWrapper}>
          <LabeledItem
            label={t`Desired Salary`}
            value={formatNumber({
              value: candidate.salary,
              currency: candidate.currentSalaryCurrency,
            })}
          />

          <LabeledItem
            label={t`Desired Location`}
            value={candidate.potentialLocations}
          />

          <LabeledItem
            label={t`Other Desired Benefits`}
            value={
              <ul>
                {candidate.otherDesiredBenefits?.map((benefit, index) => (
                  <li key={index}>
                    <ChoiceName
                      value={benefit}
                      choices={otherDesiredBenefitChoices}
                      otherChoiceValue='other'
                      otherChoiceName={candidate.otherDesiredBenefitsOthersDetail}
                      formatOtherChoice={formatOtherBenefit}
                    />
                  </li>
                ))}
              </ul>
            }
          />
        </div>

        <LabeledItem
          label={t`Expectation Details`}
          value={candidate.expectationsDetails}
          variant='textarea'
        />

        <div className={styles.jobChangePeriod}>
          <LabeledItem
            label={t`Job Change Urgency`}
            value={getChoiceName(jobChangeUrgencyChoices, candidate.jobChangeUrgency)}
          />

          <LabeledItem
            label={t`Notice Period`}
            value={getChoiceName(noticePeriodChoices, candidate.noticePeriod)}
          />
        </div>
      </div>
    </div>
  );
};

export default memo(ExpectationsSection);
