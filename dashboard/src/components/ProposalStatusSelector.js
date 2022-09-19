import React, { memo, useCallback, useMemo } from 'react';
import { connect } from 'react-redux';

import PropTypes from 'prop-types';
import _ from 'lodash';

import SelectInput from './SelectInput';

const mapStateToProps = (state) => ({
  shortlistOptions: state.settings.localeData.proposalShortlistStatuses,
  longlistOptions: state.settings.localeData.proposalLonglistStatuses,
});

const getValue = (status) => status.id;

const NON_SELECTABLE_GROUPS = ['pending_feedback', 'pending_interview'];

function ProposalStatusSelector({
  shortlistOptions,
  longlistOptions,
  noValueOption,
  value,
  stage,
  ...rest
}) {
  const usedLonglistOptions = useMemo(
    () =>
      longlistOptions.filter(
        (option) => !_.includes(NON_SELECTABLE_GROUPS, option.group)
      ),
    [longlistOptions]
  );

  const getLabel = useCallback(
    (option, placeholder) => {
      if (!option) {
        option = longlistOptions.find((item) => item.id === value);
      }
      return option ? option.status : placeholder;
    },
    [longlistOptions, value]
  );

  const options = stage === 'shortlist' ? shortlistOptions : usedLonglistOptions;

  const usedOptions = useMemo(
    () => (noValueOption ? [{ id: '', status: noValueOption }, ...options] : options),
    [options, noValueOption]
  );

  return (
    <SelectInput
      getLabel={getLabel}
      getValue={getValue}
      options={usedOptions}
      value={value}
      {...rest}
    />
  );
}

const LocalPropTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      status: PropTypes.string,
      id: PropTypes.number,
    })
  ),
};

ProposalStatusSelector.propTypes = {
  onSelect: PropTypes.func,
  noValueOption: PropTypes.string,
  shortlistOptions: LocalPropTypes.options,
  longlistOptions: LocalPropTypes.options,
  value: PropTypes.number,
  stage: PropTypes.oneOf(['shortlist', 'longlist']).isRequired,
};
ProposalStatusSelector.defaultProps = {
  noValueOption: null,
  shortlistOptions: [],
  longlistOptions: [],
};

export default connect(mapStateToProps)(memo(ProposalStatusSelector));
