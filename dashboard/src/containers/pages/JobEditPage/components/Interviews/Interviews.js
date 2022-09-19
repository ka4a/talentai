import React, { useCallback, useEffect } from 'react';
import { useParams } from 'react-router-dom';

import PropTypes from 'prop-types';
import { v4 as uuid } from 'uuid';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { useInterviewTemplatesList, useStaffOptions } from '@swrAPI';
import { DynamicList, ListItemCard } from '@components';
import { INTERVIEW_TYPES_CHOICES } from '@constants';
import { useTranslatedChoices } from '@hooks';

import styles from './Interviews.module.scss';

const Interviews = (props) => {
  const { interviews, FormInput, addFieldRow, removeFieldRow, setValue } = props;

  const { jobId } = useParams();

  const { i18n } = useLingui();
  const interviewTypesChoices = useTranslatedChoices(i18n, INTERVIEW_TYPES_CHOICES);
  // should fetch on "Create Job" form where jobId does not exist
  const shouldFetch = !jobId;
  const interviewTemplatesList = useInterviewTemplatesList(shouldFetch);
  const staffList = useStaffOptions();

  useEffect(() => {
    if (interviewTemplatesList.length) {
      // interviewTemplatesList is fetched and processed only if this is "Create Job" form
      const mappedInterviewTemplates = interviewTemplatesList.map(
        ({ interviewType, defaultOrder }) => ({
          localId: uuid(),
          order: defaultOrder,
          interviewType,
          description: '',
          interviewer: null,
        })
      );

      setValue('interviewTemplates', mappedInterviewTemplates);
    }
  }, [interviewTemplatesList, setValue]);

  const addInterview = useCallback(() => {
    addFieldRow({
      key: 'interviewTemplates',
      defaultObject: {
        order: interviews.length + 1,
        interviewType: 'general',
        description: '',
        interviewer: null,
      },
    });
  }, [addFieldRow, interviews.length]);

  const removeInterview = useCallback(
    (id) => {
      // not allowed to delete last interview
      if (interviews.length === 1) return;

      removeFieldRow(
        {
          currentTarget: { dataset: { id } },
        },
        'interviewTemplates'
      );
    },
    [interviews.length, removeFieldRow]
  );

  return (
    <DynamicList
      title={t`Interviews`}
      addRowText={t`+ Add Interview`}
      data={interviews}
      fields={[
        {
          id: 1,
          render: (index, interview) => (
            <ListItemCard
              index={index}
              onRemove={() => removeInterview(interview.id ?? interview.localId)}
              isRemoveDisabled={interviews.length === 1}
            >
              <div className={styles.row}>
                <FormInput
                  type='select'
                  name={`interviewTemplates[${index}].interviewType`}
                  label={t`Type`}
                  options={interviewTypesChoices}
                />
                <FormInput
                  type='select'
                  label={t`Interviewer`}
                  name={`interviewTemplates[${index}].interviewer`}
                  options={staffList}
                />
              </div>

              <FormInput
                type='rich-editor'
                label={t`Details`}
                name={`interviewTemplates[${index}].description`}
              />
            </ListItemCard>
          ),
        },
      ]}
      onAddRow={addInterview}
      isDeleteShown={false}
    />
  );
};

Interviews.propTypes = {
  interviews: PropTypes.array.isRequired,
  FormInput: PropTypes.func.isRequired,
  addFieldRow: PropTypes.func.isRequired,
  removeFieldRow: PropTypes.func.isRequired,
  setValue: PropTypes.func.isRequired,
};

export default Interviews;
