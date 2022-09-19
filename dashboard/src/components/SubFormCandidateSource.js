import React, { Component, useCallback, useState, useMemo } from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import _ from 'lodash';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

const LocalPropTypes = {
  arrayOfOptions: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string,
      value: PropTypes.any,
    })
  ),
};

SubFormCandidateSource.propTypes = {
  form: PropTypes.shape({
    source: PropTypes.any,
    sourceDetails: PropTypes.string,
  }),
  InputComponent: PropTypes.oneOfType([PropTypes.instanceOf(Component), PropTypes.func])
    .isRequired,
  i18n: PropTypes.shape({
    _: PropTypes.func.isRequired,
  }).isRequired,
  onChangeSource: PropTypes.func.isRequired,
  candidateSourceChoices: LocalPropTypes.arrayOfOptions,
  candidateSourceDetails: PropTypes.objectOf(
    PropTypes.shape({
      label: PropTypes.string,
      choices: LocalPropTypes.arrayOfOptions,
    })
  ),
  sourceField: PropTypes.string,
  detailField: PropTypes.string,
};

SubFormCandidateSource.defaultProps = {
  sourceField: 'source',
  detailField: 'sourceDetails',
  customDetailField: 'newSourceDetails',
};

const toOption = (value) => ({ label: value, value });

const addMissingOption = (options, value) =>
  value === '' || options.some((option) => option.value === value)
    ? options
    : [toOption(value), ...options];

function SubFormCandidateSource(props) {
  const { InputComponent, form, setValue, i18n, sourceField, detailField } = props;

  const [isOther, setIsOther] = useState(false);

  const detailsDefinitions = useSelector((state) =>
    _.get(state.settings.localeData, 'candidateSourceDetails', {})
  );

  const sources = useSelector((state) =>
    _.get(state.settings.localeData, 'candidateSourceChoices', [])
  );

  const source = _.get(form, sourceField);
  const details = _.get(form, detailField);
  const detailsDefinition = detailsDefinitions[source];

  const detailsDropdownValue = isOther ? null : details;
  const usedDetailsOptions = useMemo(
    () =>
      addMissingOption(_.get(detailsDefinition, 'choices', []), detailsDropdownValue),
    [detailsDefinition, detailsDropdownValue]
  );

  // Sets ths first option in the sourceCategory if category changes
  // and clears custom option input
  const handleChangeSource = useCallback(
    (event) => {
      const value = event.target.value;
      const detailProperties = detailsDefinitions[value];
      setValue(sourceField, event.target.value);
      if (detailProperties) {
        const detailsSelection = detailProperties.choices[0].value;
        setValue(detailField, detailsSelection);
        setIsOther(detailsSelection === null);
      } else {
        setValue(detailField, '');
        setIsOther(false);
      }
    },
    [detailsDefinitions, setValue, sourceField, detailField]
  );

  // Shows input for other value, if "Other" option is selected
  // Hides it if different option is selected
  const handleChangeDetails = useCallback(
    (event) => {
      const value = event.target.value;
      setValue(detailField, value === null ? '' : value);
      setIsOther(value === null);
    },
    [setValue, detailField]
  );

  const renderedBlocks = [
    <InputComponent
      key='source'
      type='select'
      name={sourceField}
      label={i18n._(t`Source`)}
      options={sources}
      placeholder=''
      onChange={handleChangeSource}
      searchable
      notStrictSearch
      toOption={toOption}
    />,
  ];

  if (detailsDefinition) {
    renderedBlocks.push(
      <InputComponent
        key='sourceDetails'
        type='select'
        // if "Other" option is selected, the other input would show actual value
        value={detailsDropdownValue}
        label={detailsDefinition.label}
        options={usedDetailsOptions}
        onChange={handleChangeDetails}
        placeholder=''
      />
    );

    if (isOther)
      renderedBlocks.push(
        <InputComponent
          key='sourceDetails'
          isWide
          name={detailField}
          label={detailsDefinition.labelNew}
          placeholder=''
        />
      );
  }

  return renderedBlocks;
}

export default withI18n()(SubFormCandidateSource);
