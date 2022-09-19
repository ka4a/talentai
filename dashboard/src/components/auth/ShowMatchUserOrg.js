import { memo } from 'react';
import { connect } from 'react-redux';

import PropTypes from 'prop-types';
import { compose } from 'redux';
import _ from 'lodash';

const wrapper = compose(
  memo,
  connect((state) => {
    const org = _.get(state, 'user.profile.org', {});
    return {
      userOrgId: org.id,
      userOrgType: org.type,
    };
  })
);

ShowMatchUserOrg.propTypes = {
  shouldNotEqual: PropTypes.bool,
  shouldOnlyMatchType: PropTypes.bool,
  userOrgId: PropTypes.number,
  userOrgType: PropTypes.string,
  orgId: PropTypes.number,
  orgType: PropTypes.string.isRequired,
  placeholder: PropTypes.number,
  render: PropTypes.func,
};

ShowMatchUserOrg.defaultProps = {
  shouldNotEqual: false,
  shouldOnlyMatchType: false,
  orgId: null,
  placeholder: null,
  render: null,
};

function ShowMatchUserOrg(props) {
  const {
    userOrgId,
    userOrgType,
    orgId,
    orgType,
    shouldNotEqual,
    shouldOnlyMatchType,
    children,
    placeholder,
    render,
  } = props;

  let isEqual = userOrgType === orgType;
  if (!shouldOnlyMatchType) isEqual = isEqual && userOrgId === orgId;

  if (render) return render(isEqual);

  return isEqual === shouldNotEqual ? placeholder : children;
}

export default wrapper(ShowMatchUserOrg);
