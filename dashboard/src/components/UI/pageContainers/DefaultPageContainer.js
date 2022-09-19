import React, { memo } from 'react';
import { useSelector } from 'react-redux';
import { Breadcrumb } from 'reactstrap';

import PropTypes from 'prop-types';

import { joinTitle } from './utils';
import PageContainer from './PageContainer';

const DefaultPageContainer = ({ title, colAttrs, breadcrumb, children }) => {
  const user = useSelector((state) => state.user);

  const fullTitle = joinTitle([title, user?.profile?.org?.name, 'ZooKeep']);

  return (
    <PageContainer title={fullTitle} colAttrs={colAttrs}>
      {breadcrumb && (
        <div className='breadcrumb-custom-container'>
          <Breadcrumb className='my-auto'>{breadcrumb}</Breadcrumb>
        </div>
      )}

      {children}
    </PageContainer>
  );
};

DefaultPageContainer.propTypes = {
  title: PropTypes.string,
  breadcrumb: PropTypes.element,
  colAttrs: PropTypes.object,
};

DefaultPageContainer.defaultProps = {
  title: '',
  breadcrumb: null,
  colAttrs: null,
};

export default memo(DefaultPageContainer);
