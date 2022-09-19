import React from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { LabeledItem } from '@components';
import { getChoiceName, getFormattedDate } from '@utils';
import formStyles from '@styles/form.module.scss';
import { useTranslatedChoices } from '@hooks';
import { JOB_EMPLOYMENT_TYPE_CHOICES } from '@constants';

function PrivateDetails({ job }) {
  const { i18n } = useLingui();
  const jobEmploymentTypeChoices = useTranslatedChoices(
    i18n,
    JOB_EMPLOYMENT_TYPE_CHOICES
  );

  return (
    <>
      <div className={classnames(formStyles.rowWrapper, formStyles.firstElementThree)}>
        <LabeledItem label={t`Job Title`} value={job.title} />
        <LabeledItem label={t`Function`} value={job.function?.title} />
      </div>

      <div className={classnames(formStyles.rowWrapper, formStyles.topGap)}>
        <LabeledItem
          label={t`Employment Type`}
          value={getChoiceName(jobEmploymentTypeChoices, job.employmentType)}
        />
        <LabeledItem label={t`Department`} value={job.department} />
        <LabeledItem label={t`Reason for Opening`} value={job.reasonForOpening} />
        <LabeledItem
          label={t`Target Hiring Date`}
          value={getFormattedDate(job.targetHiringDate)}
        />
      </div>

      <hr className={classnames(formStyles.topGap, formStyles.bottomGap)} />
    </>
  );
}

PrivateDetails.propTypes = {
  job: PropTypes.object.isRequired,
};

export default PrivateDetails;
