import React, { useCallback } from 'react';

import moment from 'moment';
import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';

import { FormSection, DynamicList, ListItemCard } from '@components';

import styles from '../CandidateForm/CandidateForm.module.scss';

const formKey = 'experienceDetails';

const ExperienceDetails = ({ data, FormInput, addFieldRow, removeFieldRow }) => {
  const addExperience = useCallback(() => {
    addFieldRow({
      key: formKey,
      defaultObject: {
        occupation: '',
        company: '',
        summary: '',
        currentlyPursuing: false,
        dateStart: null,
        dateEnd: null,
      },
    });
  }, [addFieldRow]);

  const removeExperience = useCallback(
    (id) => {
      removeFieldRow({ currentTarget: { dataset: { id } } }, formKey);
    },
    [removeFieldRow]
  );

  return (
    <FormSection id='experience-details-edit' title={t`Experience Details`}>
      <DynamicList
        data={data}
        fields={[
          {
            id: 1,
            render: (index, experience) => (
              <ListItemCard
                index={index}
                // localId is assigned in processReadObject (CandidateForm)
                onRemove={() => removeExperience(experience.localId)}
              >
                <div className={classnames([styles.rowWrapper, styles.twoElements])}>
                  <FormInput
                    label={t`Job Title`}
                    name={`${formKey}[${index}].occupation`}
                    placeholder={t`e.g. Software Developer`}
                    onBlur={null}
                    required
                  />
                  <FormInput
                    label={t`Company`}
                    name={`${formKey}[${index}].company`}
                    placeholder={t`e.g. Netflix`}
                    onBlur={null}
                    required
                  />
                </div>

                <div
                  className={classnames([
                    styles.rowWrapper,
                    styles.topGap,
                    styles.twoElements,
                  ])}
                >
                  <FormInput
                    type='simple-datepicker'
                    name={`${formKey}[${index}].dateStart`}
                    label={t`Start Date`}
                    format='YYYY-MM-DD'
                    maxDate={moment().toDate()}
                    required
                  />

                  <div className={styles.checkboxWrapper}>
                    <FormInput
                      type='checkbox'
                      name={`${formKey}[${index}].currentlyPursuing`}
                      label={t`Current`}
                    />
                  </div>
                </div>

                <div
                  className={classnames([
                    styles.rowWrapper,
                    styles.topGap,
                    styles.twoElements,
                  ])}
                >
                  <FormInput
                    type='simple-datepicker'
                    name={`${formKey}[${index}].dateEnd`}
                    label={t`End Date`}
                    format='YYYY-MM-DD'
                    isDisabled={data[index].currentlyPursuing}
                  />
                  <FormInput
                    label={t`Location`}
                    name={`${formKey}[${index}].location`}
                    onBlur={null}
                  />
                </div>

                <FormInput
                  type='rich-editor'
                  wrapperClassName={styles.topGap}
                  name={`${formKey}[${index}].summary`}
                  label={t`Responsibilities`}
                />
              </ListItemCard>
            ),
          },
        ]}
        onAddRow={addExperience}
        addRowText={t`+ Add Experience`}
        isDeleteShown={false}
      />
    </FormSection>
  );
};

ExperienceDetails.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  FormInput: PropTypes.func.isRequired,
  addFieldRow: PropTypes.func.isRequired,
  removeFieldRow: PropTypes.func.isRequired,
};

export default ExperienceDetails;
