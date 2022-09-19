import React, { memo } from 'react';
import { HiLocationMarker } from 'react-icons/hi';
import { Container } from 'reactstrap';
import { Link as ScrollLink } from 'react-scroll';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { getChoiceName } from '@utils';
import { JOB_EMPLOYMENT_TYPE_CHOICES } from '@constants';
import { Typography, InfoTag, FormattedSalary, Button } from '@components';
import { useTranslatedChoices } from '@hooks';

import styles from './JobPostingHeader.module.scss';

const JobPostingHeader = ({
  job,
  shouldShowApply,
  shouldShowSalary,
  backNavButton,
}) => {
  const {
    title,
    clientName,
    employmentType,
    function: functionValue,
    workLocation,
    salaryTo,
    salaryFrom,
    salaryPer,
  } = job;

  const { i18n } = useLingui();
  const jobEmploymentChoices = useTranslatedChoices(i18n, JOB_EMPLOYMENT_TYPE_CHOICES);

  const employmentTypeValue = getChoiceName(jobEmploymentChoices, employmentType);

  return (
    <div className={styles.header}>
      <Container>
        {backNavButton}
        <div className={styles.wrapper}>
          <div>
            <div className={styles.titleWrapper}>
              <Typography variant='h1'>{title}</Typography>
              {clientName && <Typography variant='bodyStrong'>{clientName}</Typography>}
            </div>

            {(employmentTypeValue || workLocation) && (
              <div className={styles.description}>
                {employmentTypeValue && (
                  <Typography variant='bodyStrong' className={styles.employment}>
                    {employmentTypeValue}
                  </Typography>
                )}

                {workLocation && (
                  <Typography variant='bodyStrong' className={styles.location}>
                    <HiLocationMarker />
                    {workLocation}
                  </Typography>
                )}
              </div>
            )}
          </div>

          <div className={styles.rightWrapper}>
            <div className={styles.rightInfo}>
              {functionValue && <InfoTag>{functionValue?.title}</InfoTag>}

              {shouldShowSalary && salaryTo && salaryFrom && (
                <InfoTag>
                  <FormattedSalary job={job} hidePerName />
                  <span>&nbsp;{`/ ${salaryPer}`}</span>
                </InfoTag>
              )}
            </div>

            {shouldShowApply && (
              <ScrollLink to='application' duration={500} offset={-21} smooth>
                <Button>
                  <Trans>Apply</Trans>
                </Button>
              </ScrollLink>
            )}
          </div>
        </div>
      </Container>
    </div>
  );
};

JobPostingHeader.propTypes = {
  job: PropTypes.shape({}).isRequired,
  shouldShowApply: PropTypes.bool,
  shouldShowSalary: PropTypes.bool,
  backNavButton: PropTypes.node,
};

JobPostingHeader.defaultProps = {
  shouldShowApply: false,
  shouldShowSalary: false,
};

export default memo(JobPostingHeader);
