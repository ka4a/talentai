import React, { Component, useMemo } from 'react';
import { useSelector } from 'react-redux';

import PropTypes from 'prop-types';
import _ from 'lodash';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

BillDescriptionInputSet.propTypes = {
  contractType: PropTypes.string.isRequired,
  Input: PropTypes.oneOfType([PropTypes.instanceOf(Component), PropTypes.func])
    .isRequired,
  name: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  isPlacementExists: PropTypes.func.isRequired,
};

const OTHER_VALUE = '';

const wrapper = withI18n();

function BillDescriptionInputSet(props) {
  const { contractType, Input, name, isPlacementExists, value, i18n } = props;

  const optionsMap = useSelector((state) => state.settings.localeData.billDescriptions);

  const labelOther = i18n._(t`Other`);

  const options = useMemo(() => {
    const availableOptions = _.get(optionsMap, contractType, []);
    return [
      ..._.filter(
        availableOptions,
        (option) => option.forPlacement === isPlacementExists
      ),
      { label: labelOther, value: OTHER_VALUE }, // "other" option would trigger Bill Description input to show up
    ];
  }, [contractType, optionsMap, isPlacementExists, labelOther]);

  const selection = useMemo(() => {
    const option = _.find(options, { value });
    return option ? value : OTHER_VALUE;
  }, [value, options]);

  return (
    <>
      <Input
        label={i18n._(t`Bill Description`)}
        type='select'
        value={selection}
        name={name}
        options={options}
      />
      {selection === OTHER_VALUE ? (
        <Input label={i18n._(t`Custom Bill Description`)} name={name} />
      ) : null}
    </>
  );
}

export default wrapper(BillDescriptionInputSet);
