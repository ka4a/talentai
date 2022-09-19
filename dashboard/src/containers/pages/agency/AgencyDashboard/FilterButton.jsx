import React, { memo } from 'react';
import PropTypes from 'prop-types';
import ButtonTableMenu from '../../../../components/ButtonTableMenu/ButtonTableMenu';

FilterButton.propTypes = {
  value: PropTypes.string,
};

function FilterButton(props) {
  const { value } = props;

  return <ButtonTableMenu>{value}</ButtonTableMenu>;
}

export default memo(FilterButton);
