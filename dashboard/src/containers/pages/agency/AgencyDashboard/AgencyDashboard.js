import React from 'react';

import { client } from '@client';
import { fetchErrorHandler } from '@utils';
import { DefaultPageContainer } from '@components';

import JobsTable from './JobsTable';

class AgencyDashboard extends React.Component {
  state = {
    clients: [],
  };

  componentDidMount() {
    this.fetchClients();
  }

  fetchClients = () => {
    client
      .execute({
        operationId: 'clients_list',
      })
      .then((response) => {
        const clients = response.obj.results;

        this.setState({ clients });
      })
      .catch(fetchErrorHandler);
  };

  render() {
    const { clients } = this.state;

    return (
      <DefaultPageContainer title='Jobs'>
        <JobsTable clients={clients} />
      </DefaultPageContainer>
    );
  }
}

export default AgencyDashboard;
