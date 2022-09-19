import React, { memo } from 'react';
import { useSelector } from 'react-redux';
import { Redirect } from 'react-router';
import { Button } from 'reactstrap';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { openZendeskForm } from '@utils';
import { DefaultPageContainer } from '@components';

const NotFoundPage = memo(({ inline }) => {
  const isAuthenticated = useSelector((state) => state.user.isAuthenticated);

  const content = (
    <>
      <div className='text-center'>
        <h2 className='m-0 mb-16'>
          <Trans>404 Not Found</Trans>
        </h2>

        <div>
          <Trans>Sorry, an error has occurred, the requested page was not found!</Trans>
        </div>

        <Button color='link' className='text-secondary p-0' onClick={openZendeskForm}>
          <Trans>Contact Support</Trans>
        </Button>
      </div>
    </>
  );

  if (!isAuthenticated) return <Redirect to='/login' />;

  return inline ? (
    content
  ) : (
    <DefaultPageContainer title='404 - Not Found'>{content}</DefaultPageContainer>
  );
});

NotFoundPage.propTypes = {
  inline: PropTypes.bool,
};

NotFoundPage.defaultProps = {
  inline: false,
};

export default memo(NotFoundPage);
