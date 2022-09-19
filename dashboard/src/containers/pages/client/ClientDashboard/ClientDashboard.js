import React from 'react';
import { Container } from 'reactstrap';

import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { HIRING_MANAGERS, TALENT_ASSOCIATES } from '@constants';
import { DefaultPageContainer } from '@components';

import ActiveJobsTable from './ActiveJobsTable';
import ProposalsTable from './ProposalsTable';
import ShowAuthenticated from '../../../../components/auth/ShowAuthenticated';

class ClientDashboard extends React.Component {
  render() {
    return (
      <DefaultPageContainer title={this.props.i18n._(t`Dashboard`)}>
        <ShowAuthenticated groups={[TALENT_ASSOCIATES]}>
          <ActiveJobsTable />
        </ShowAuthenticated>

        <Container className='p-0'>
          <div className='mt-24'>
            <ShowAuthenticated groups={[HIRING_MANAGERS]}>
              <ProposalsTable isTalentAssociate={false} />
            </ShowAuthenticated>

            <ShowAuthenticated groups={[TALENT_ASSOCIATES]}>
              <ProposalsTable isTalentAssociate={true} />
            </ShowAuthenticated>
          </div>
        </Container>
      </DefaultPageContainer>
    );
  }
}

export default withI18n()(ClientDashboard);
