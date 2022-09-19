import React, { useCallback } from 'react';
import { Col, Row } from 'reactstrap';

import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import { useSwagger } from '@hooks';
import { DefaultPageContainer, ReqStatus } from '@components';

import AgencyClientEditForm from './AgencyClientEditForm';

function AgencyClientEditPage(props) {
  const clientId = props.match.params.clientId;
  const redirect = props.history.push;

  const { obj: client, loading, errorObj } = useSwagger('clients_read', {
    id: clientId,
  });

  const onSaved = useCallback(() => {
    redirect('/a/clients/');
  }, [redirect]);

  const title =
    client === null
      ? props.i18n._(t`Loading...`)
      : props.i18n._(t`Edit ${client.name}`);

  if (!client || errorObj) {
    return <ReqStatus {...{ loading, error: errorObj }} />;
  }

  return (
    <DefaultPageContainer title={title}>
      <Row>
        <Col xs={12} lg={{ offset: 2, size: 8 }}>
          <h2>{title}</h2>
          <AgencyClientEditForm editingId={clientId} onSaved={onSaved} />
        </Col>
      </Row>
    </DefaultPageContainer>
  );
}

export default withI18n()(AgencyClientEditPage);
