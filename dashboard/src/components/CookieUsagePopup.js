import React from 'react';
import { Link } from 'react-router-dom';
import { connect } from 'react-redux';

import { Trans } from '@lingui/macro';

import { Button } from '@components';
import { setCookieUsageFlag } from '@actions';

const mapDispatchToProps = (dispatch) => ({
  setCookieUsageFlag: () => dispatch(setCookieUsageFlag(true)),
});

const CookieUsagePopup = ({ setCookieUsageFlag }) => (
  <div className='cookie-notice'>
    <div className='d-flex justify-content-between align-items-center'>
      <div>
        <strong>
          <Trans>Cookie usage</Trans>
        </strong>
        <br />
        <Trans>
          This site requires cookies and 3rd-party services to function properly. To
          continue, you must agree to our
          <span>&nbsp;</span>
          <Link to='/legal/privacy-policy'>Privacy Policy</Link>.
        </Trans>
      </div>
      <div>
        <Button onClick={setCookieUsageFlag}>
          <Trans>Agree</Trans>
        </Button>
      </div>
    </div>
  </div>
);

export default connect(null, mapDispatchToProps)(CookieUsagePopup);
