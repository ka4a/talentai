import React, { useCallback } from 'react';

import classnames from 'classnames';
import PropTypes from 'prop-types';
import { t } from '@lingui/macro';
import differenceBy from 'lodash/differenceBy';
import { useLingui } from '@lingui/react';

import { JOB_STATUS_CHOICES } from '@constants';
import { FormSection, DynamicList } from '@components';
import { useTranslatedChoices } from '@hooks';
import { useManagersList, useStaffOptions } from '@swrAPI';

import Interviews from '../Interviews';

import styles from '../JobForm/JobForm.module.scss';

const HiringProcess = (props) => {
  const {
    FormInput,
    disableReason,
    setOpeningsCount,
    form,
    setValue,
    addFieldRow,
    removeFieldRow,
  } = props;

  const managersList = useManagersList();
  const staffList = useStaffOptions();

  const { i18n } = useLingui();
  const jobStatusChoices = useTranslatedChoices(i18n, JOB_STATUS_CHOICES);

  const addRow = useCallback(
    (formKey, valueKey) => () => {
      addFieldRow({
        key: formKey,
        defaultObject: { [valueKey]: '' },
      });
    },
    [addFieldRow]
  );

  const removeRow = useCallback(
    (formKey) => (event) => {
      removeFieldRow(event, formKey);
    },
    [removeFieldRow]
  );

  const getRecruitersOptions = useCallback(
    (idx) => {
      const selectedRecruiters = form.recruiters.map((el) => ({ value: el.recruiter }));
      const freeOptions = differenceBy(staffList, selectedRecruiters, 'value');

      const selectedOption = staffList.find(
        (el) => el.value === form.recruiters[idx].recruiter
      );

      if (selectedOption) freeOptions.push(selectedOption);

      return freeOptions;
    },
    [form.recruiters, staffList]
  );

  return (
    <FormSection id='hiring-process-edit' title={t`Hiring Process`}>
      <div className={classnames([styles.rowWrapper, styles.hiringManagerWrapper])}>
        <FormInput
          type='select'
          label={t`Hiring Manager`}
          name='managers[0]'
          options={managersList}
        />
        <FormInput
          name='openingsCount'
          label={t`No. of Openings`}
          disabled={disableReason.openingsCount != null}
          containerTooltip={disableReason.openingsCount}
          onChange={setOpeningsCount}
          required
        />
        <FormInput
          type='select'
          name='status'
          label={t`Job Status`}
          options={jobStatusChoices}
          containerTooltip={disableReason.status}
          disabled={disableReason.status != null}
        />
      </div>

      <hr />

      <DynamicList
        title={t`Internal Recruiters`}
        addRowText={t`+ Add Recruiter`}
        data={form.recruiters}
        fields={[
          {
            id: 1,
            render: (idx) => (
              <FormInput
                type='select'
                label={t`Recruiter`}
                name={`recruiters[${idx}].recruiter`}
                value={form.recruiters[idx].recruiter}
                options={getRecruitersOptions(idx)}
              />
            ),
          },
        ]}
        onAddRow={addRow('recruiters', 'recruiter')}
        onRemoveRow={removeRow('recruiters')}
      />

      <hr />

      <DynamicList
        title={t`Hiring Criteria`}
        addRowText={t`+ Add Hiring Criteria`}
        data={form.hiringCriteria}
        fields={[
          {
            id: 1,
            render: (idx) => (
              <FormInput label={String(idx + 1)} name={`hiringCriteria[${idx}].name`} />
            ),
          },
        ]}
        onAddRow={addRow('hiringCriteria', 'name')}
        onRemoveRow={removeRow('hiringCriteria')}
      />

      <hr />

      <DynamicList
        title={t`Screening questions`}
        addRowText={t`+ Add Screening Question`}
        data={form.questions}
        fields={[
          {
            id: 1,
            render: (idx) => (
              <FormInput label={String(idx + 1)} name={`questions[${idx}].text`} />
            ),
          },
        ]}
        onAddRow={addRow('questions', 'text')}
        onRemoveRow={removeRow('questions')}
      />

      <hr />

      <Interviews
        interviews={form.interviewTemplates}
        {...{ FormInput, addFieldRow, removeFieldRow, setValue }}
      />

      <hr />

      <FormInput
        type='rich-editor'
        label={t`Hiring Process Notes`}
        name={`hiringProcess`}
      />
    </FormSection>
  );
};

HiringProcess.propTypes = {
  FormInput: PropTypes.func.isRequired,
  disableReason: PropTypes.shape({
    openingsCount: PropTypes.number,
    status: PropTypes.string,
  }).isRequired,
  form: PropTypes.shape({}).isRequired,
  setValue: PropTypes.func.isRequired,
  addFieldRow: PropTypes.func.isRequired,
  removeFieldRow: PropTypes.func.isRequired,
  setOpeningsCount: PropTypes.func.isRequired,
};

export default HiringProcess;
