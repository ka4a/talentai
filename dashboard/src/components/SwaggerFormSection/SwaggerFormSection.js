import React, { memo } from 'react';
import { Row } from 'reactstrap';

import PropTypes from 'prop-types';

import { FormSectionOld } from '../FormSectionOld';

SwaggerFormSection.propTypes = {
  title: PropTypes.string,
};

function SwaggerFormSection(props) {
  const { title, children } = props;

  return (
    <div>
      {title ? <FormSectionOld>{title}</FormSectionOld> : null}
      <Row form>{children}</Row>
      <hr className='my-24' />
    </div>
  );
}

export default memo(SwaggerFormSection);
