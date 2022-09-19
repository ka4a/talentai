import React from 'react';

import PropTypes from 'prop-types';
import classNames from 'classnames';
import { useLingui } from '@lingui/react';

import { PIPELINE_ITEMS_CHOICES, PROPOSAL_STAGES } from '@constants';
import { useTranslatedChoices } from '@hooks';
import { Typography } from '@components';

import styles from './ProposalsPipeline.module.scss';

const PipelineItem = ({ itemKey, label, value, valueColor, openingsCount }) => {
  const isHiredStage = itemKey === PROPOSAL_STAGES.hired;
  const formattedLabel = () => {
    if (label === 'Pre-Screening') {
      return (
        <span>
          <span className={styles.label}>Pre</span>
          <span className={styles.label}>&#8209;</span>
          <span className={styles.label}>Screening</span>
        </span>
      );
    }

    return label;
  };

  return (
    <>
      <span
        className={classNames(styles.item, {
          [styles.hiredItem]: isHiredStage,
        })}
      >
        <Typography className={styles.value}>
          <span className={styles[itemKey]} style={{ color: valueColor }}>
            {value}
            {isHiredStage ? `/${openingsCount}` : ''}
          </span>
        </Typography>

        <Typography
          variant='caption'
          className={classNames([styles.label, styles[itemKey]])}
        >
          {formattedLabel()}
        </Typography>
      </span>
    </>
  );
};

const ProposalsPipeline = (props) => {
  const { pipeline, openingsCount, valueColor, jobOrgType, isCard } = props;

  const { i18n } = useLingui();
  const pipelineItemsChoices = useTranslatedChoices(i18n, PIPELINE_ITEMS_CHOICES);

  return (
    <div className={classNames({ [styles.card]: isCard })}>
      <div className={classNames([styles.wrapper, { container: isCard }])}>
        {pipelineItemsChoices.map(({ value, name }) => {
          const shouldShowItem = value !== 'preScreening' && jobOrgType !== 'agency';
          return (
            shouldShowItem && (
              <PipelineItem
                key={value}
                itemKey={value}
                label={name}
                value={pipeline[value]}
                valueColor={valueColor}
                openingsCount={openingsCount}
              />
            )
          );
        })}
      </div>
    </div>
  );
};

ProposalsPipeline.propTypes = {
  pipeline: PropTypes.shape({
    associated: PropTypes.number,
    hired: PropTypes.number,
    interviewing: PropTypes.number,
    offering: PropTypes.number,
    preScreening: PropTypes.number,
    rejected: PropTypes.number,
    screening: PropTypes.number,
    submissions: PropTypes.number,
  }),
  isCard: PropTypes.bool,
  valueColor: PropTypes.string,
  openingsCount: PropTypes.number,
  jobOrgType: PropTypes.string,
};

ProposalsPipeline.defaultProps = {
  pipeline: {},
  valueColor: '#292D45',
  openingsCount: 0,
  jobOrgType: '',
  isCard: false,
};

export default ProposalsPipeline;
