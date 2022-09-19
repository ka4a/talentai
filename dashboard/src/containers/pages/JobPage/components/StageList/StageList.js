import React, { memo, useCallback, useMemo } from 'react';
import { useHistory } from 'react-router';
import { useParams } from 'react-router-dom';

import { t } from '@lingui/macro';
import classnames from 'classnames';
import PropTypes from 'prop-types';
import { useLingui } from '@lingui/react';

import { LANGUAGE_LEVEL_CHOICES } from '@constants';
import { useGetJob } from '@swrAPI';
import {
  Avatar,
  CandidateCurrentJob,
  FormattedSalary,
  Table,
  Typography,
} from '@components';
import { useTranslatedChoices } from '@hooks';

import StatusCell from './components/StatusCell';

import styles from './StageList.module.scss';

const wrapCaption = (children, className) => (
  <Typography className={className} variant='caption'>
    {children}
  </Typography>
);

const StageList = ({ data }) => {
  const history = useHistory();
  const { proposalId } = useParams();

  const { data: job } = useGetJob();

  const goToProposal = useCallback(
    (event, proposal) => {
      history.push(`/job/${job.id}/proposal/${proposal.id}`);
    },
    [history, job.id]
  );

  const { i18n } = useLingui();
  const languageLevelChoices = useTranslatedChoices(i18n, LANGUAGE_LEVEL_CHOICES);

  const tableColumns = [
    {
      width: 320,
      text: t`Name`,
      dataField: 'candidate',
      formatter: (candidate, proposal, { isActive }) => (
        <div className={styles.nameWrapper}>
          <Avatar
            shape='circle'
            size='xs'
            src={candidate.photo}
            className={styles.avatar}
          />
          <Typography
            variant='bodyStrong'
            className={classnames(styles.name, { [styles.whiteText]: isActive })}
          >
            {candidate.name}
          </Typography>
        </div>
      ),
    },
    {
      width: 300,
      text: t`Status`,
      dataField: 'status',
      formatter: (cell, proposal) => <StatusCell proposal={proposal} />,
    },
    {
      width: 320,
      hideInSidebar: true,
      text: t`Current job`,
      dataField: 'candidate',
      formatter: (candidate) => <CandidateCurrentJob candidate={candidate} />,
    },
    {
      width: 190,
      hideInSidebar: true,
      text: t`Japanese Fluency`,
      dataField: 'candidate.languages',
      formatter: (languages) => {
        const japaneseLanguage = languages.find((el) => el.language === 'ja');

        if (!japaneseLanguage) return wrapCaption('-', styles.caption);

        const fluency = languageLevelChoices.find(
          (el) => el.value === japaneseLanguage.level
        );
        return wrapCaption(fluency.name, styles.caption);
      },
    },
    {
      width: 180,
      hideInSidebar: true,
      text: t`Desired Salary`,
      dataField: 'candidate.salary',
      formatter: (salary, proposal) =>
        salary &&
        wrapCaption(
          <FormattedSalary job={proposal.candidate} single={true} />,
          styles.caption
        ),
    },
    {
      text: t`Source`,
      dataField: 'candidate.source',
      hideInSidebar: true,
      formatter: (source) => wrapCaption(source, styles.caption),
    },
  ];

  const tableData = useMemo(
    () => ({
      data: { results: data },
    }),
    [data]
  );

  return (
    <Table
      data={tableData}
      columns={tableColumns}
      onRowClick={goToProposal}
      isOpenColumn={Boolean(proposalId)}
      activeRowId={Number(proposalId)}
      noDataMessage=''
      hidePagination
    />
  );
};

StageList.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
};

export default memo(StageList);
