import React, { memo } from 'react';

import PropTypes from 'prop-types';
import _ from 'lodash';

import { getCssColorForId } from '@utils';

function AgencyLogo({ agency }) {
  const { id, logo } = agency;

  return (
    <div
      className={logo ? 'agency-logo' : 'agency-logo logo-noimage'}
      style={{
        backgroundImage: logo ? `url(${logo})` : '',
        backgroundColor: getCssColorForId(id),
      }}
    >
      {!logo ? _.slice(agency.name, 0, 1) : null}
    </div>
  );
}

AgencyLogo.propTypes = {
  agency: PropTypes.shape({
    id: PropTypes.number,
    logo: PropTypes.string,
  }),
};

AgencyLogo.defaultProps = {
  agency: {
    id: 0,
    logo: '',
  },
};

export default memo(AgencyLogo);
