import React from 'react';
import { Tooltip } from 'reactstrap';

import PropTypes from 'prop-types';
import _ from 'lodash';

export default class SimpleTooltip extends React.PureComponent {
  state = { open: false };

  constructor(props) {
    super(props);
    this.tooltipId = _.uniqueId('SimpleTooltip_');
  }

  toggle = () => this.setState({ open: !this.state.open });

  render() {
    const { open } = this.state;
    const { onClick, content, children, placement, className } = this.props;

    return (
      <>
        <span id={this.tooltipId} className={className} onClick={onClick}>
          {children}
        </span>
        <Tooltip
          placement={placement}
          isOpen={open}
          target={this.tooltipId}
          toggle={this.toggle}
        >
          {content}
        </Tooltip>
      </>
    );
  }
}

SimpleTooltip.propTypes = {
  content: PropTypes.node.isRequired,
  className: PropTypes.string,
  placement: PropTypes.string,
  onClick: PropTypes.func,
};

SimpleTooltip.defaultProps = {
  className: '',
};
