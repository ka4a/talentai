import React, { memo } from 'react';
import { useTitle } from 'react-use';
import { Col, Container, Row } from 'reactstrap';

import PropTypes from 'prop-types';

const PageContainer = ({ title, colAttrs, children }) => {
  useTitle(title);

  return (
    <Container fluid={true} className='main-container'>
      <Row className='p-0'>
        <Col className='p-0' {...colAttrs}>
          {children}
        </Col>
      </Row>
    </Container>
  );
};

PageContainer.propTypes = {
  title: PropTypes.string.isRequired,
  colAttrs: PropTypes.object,
};

PageContainer.defaultProps = {
  colAttrs: null,
};

export default memo(PageContainer);
