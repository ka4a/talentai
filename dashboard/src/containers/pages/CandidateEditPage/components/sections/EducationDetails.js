import React, { useCallback } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';

import { FormSection, DynamicList, ListItemCard } from '@components';

import styles from '../CandidateForm/CandidateForm.module.scss';

const formKey = 'educationDetails';

const EducationDetails = ({ data, FormInput, addFieldRow, removeFieldRow }) => {
  const addEducation = useCallback(() => {
    addFieldRow({
      key: formKey,
      defaultObject: {
        institute: '',
        department: '',
        degree: '',
        currentlyPursuing: false,
        dateEnd: null,
      },
    });
  }, [addFieldRow]);

  const removeEducation = useCallback(
    (id) => {
      removeFieldRow({ currentTarget: { dataset: { id } } }, formKey);
    },
    [removeFieldRow]
  );

  return (
    <FormSection id='education-details-edit' title={t`Education Details`}>
      <DynamicList
        data={data}
        fields={[
          {
            id: 1,
            render: (index, education) => (
              <ListItemCard
                index={index}
                // localId is assigned in processReadObject (CandidateForm)
                onRemove={() => removeEducation(education.localId)}
              >
                <div className={classnames([styles.rowWrapper, styles.twoElements])}>
                  <FormInput
                    label={t`Degree`}
                    name={`${[formKey]}[${index}].degree`}
                    placeholder={t`e.g. Bachelor`}
                    onBlur={null}
                    required
                  />
                  <FormInput
                    label={t`Institution Name`}
                    name={`${[formKey]}[${index}].institute`}
                    placeholder={t`e.g. MIT`}
                    onBlur={null}
                    required
                  />
                </div>

                <div className={styles.topGap}>
                  <FormInput
                    label={t`Field of Study`}
                    name={`${[formKey]}[${index}].department`}
                    placeholder={t`e.g. Computer Science`}
                    onBlur={null}
                  />
                </div>

                <div className={classnames([styles.topGap, styles.halfWidth])}>
                  <FormInput
                    type='simple-datepicker'
                    name={`${formKey}[${index}].dateEnd`}
                    label={t`Year Completed (or Expected)`}
                    dateInputFormat='y'
                    format='YYYY-MM-DD'
                    showYearPicker
                    required
                  />
                </div>
              </ListItemCard>
            ),
          },
        ]}
        onAddRow={addEducation}
        addRowText={t`+ Add Education`}
        isDeleteShown={false}
      />
    </FormSection>
  );
};

EducationDetails.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  FormInput: PropTypes.func.isRequired,
  addFieldRow: PropTypes.func.isRequired,
  removeFieldRow: PropTypes.func.isRequired,
};

export default EducationDetails;
