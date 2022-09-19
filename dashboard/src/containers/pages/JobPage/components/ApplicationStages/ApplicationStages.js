import React, { memo } from 'react';

import groupBy from 'lodash/groupBy';
import { defineMessage } from '@lingui/macro';

import { useGetJob, useProposalsList } from '@swrAPI';
import { JobStatusesAccordion } from '@components';
import { PROPOSAL_STAGES } from '@constants';

import InterviewingStage from '../InterviewingStage';
import StageList from '../StageList';

const STAGE_LIST = [
  {
    title: defineMessage({ message: 'Hired' }).id,
    stage: 'hired',
    titleClassname: 'hired',
  },
  { title: defineMessage({ message: 'Offering' }).id, stage: 'offering' },
  { title: defineMessage({ message: 'Interviewing' }).id, stage: 'interviewing' },
  { title: defineMessage({ message: 'Submissions' }).id, stage: 'submissions' },
  { title: defineMessage({ message: 'Screening' }).id, stage: 'screening' },
  { title: defineMessage({ message: 'Pre-Screening' }).id, stage: 'pre-screening' },
  { title: defineMessage({ message: 'Associated' }).id, stage: 'associated' },
  {
    title: defineMessage({ message: 'Rejected' }).id,
    stage: 'rejected',
    titleClassname: 'rejected',
  },
];

const useGetGroupedStages = () => {
  const { data } = useProposalsList();

  return {
    ...data,
    results: groupBy(data.results, (el) => {
      if (el.isRejected) return 'rejected';
      return el.stage;
    }),
  };
};

const ApplicationStages = () => {
  const { data: job } = useGetJob();
  const { organization } = job;

  const stages = useGetGroupedStages();

  return STAGE_LIST.map(({ title, stage, titleClassname = '' }) => {
    const isPreScreening = stage === PROPOSAL_STAGES.preScreening;
    const isPreScreeningShown = isPreScreening && organization.type === 'agency';

    const applications = stages.results[stage] ?? [];

    if (stage === PROPOSAL_STAGES.interviewing) {
      return <InterviewingStage key={stage} data={applications} />;
    }

    if (!isPreScreening || isPreScreeningShown) {
      return (
        <JobStatusesAccordion
          key={stage}
          title={title}
          count={applications.length}
          totalCount={stage === PROPOSAL_STAGES.hired ? job.openingsCount : null}
          titleClassname={titleClassname}
          disabled={!applications.length}
          content={<StageList data={applications} />}
          isOpen={applications.length > 0}
        />
      );
    }

    return null;
  });
};

ApplicationStages.propTypes = {};

export default memo(ApplicationStages);
