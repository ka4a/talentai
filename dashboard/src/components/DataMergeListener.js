import React from 'react';

import _ from 'lodash';

import DataMergeModal from './modals/DataMergeModal';

export default class DataMergeListener extends React.Component {
  state = { dataIds: [] };

  onMessage = (event) => {
    const { data } = event;

    if (data.type === 'TAB_OPEN_DATA_MERGE') {
      this.setState((state) => ({
        dataIds: [...state.dataIds, data.dataId],
      }));
    }
  };

  onModalClosed = (dataId) => {
    this.setState((state) => ({
      dataIds: _.filter(state.dataIds, (id) => id !== dataId),
    }));
  };

  componentDidMount() {
    window.addEventListener('message', this.onMessage);
  }

  componentWillUnmount() {
    window.removeEventListener('message', this.onMessage);
  }

  render() {
    const { dataIds } = this.state;
    return _.map(dataIds, (id) => (
      <DataMergeModal key={id} editingId={id} onClosed={() => this.onModalClosed(id)} />
    ));
  }
}
