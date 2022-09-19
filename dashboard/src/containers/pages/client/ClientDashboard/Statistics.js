import React from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';

import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { fetchLoadingWrapper } from '@components/ReqStatus';
import { client } from '@client';

const CARDS = [
  { key: 'liveJobs', label: t`Live Jobs` },
  { key: 'totalCandidatesSubmitted', label: t`Total candidates submitted` },
  { key: 'pendingCvReview', label: t`Pending CV review` },
  { key: 'interviewing', label: t`Interviewing` },
  { key: 'offerStage', label: t`Offer stage` },
  { key: 'wins', label: t`Wins` },
];

class Statistics extends React.Component {
  state = { data: null };

  fetchData = fetchLoadingWrapper(() =>
    client
      .execute({
        operationId: 'dashboard_get_statistics',
      })
      .then((response) => {
        this.setState({ data: response.obj });
      })
  ).bind(this);

  componentDidMount() {
    this.fetchData();
  }

  render() {
    const { data } = this.state;
    const { i18n } = this.props;

    const formattedNumber = i18n.number(data?.card?.key);

    if (data === null) return null;

    return (
      <Row>
        {CARDS.map((card) => (
          <Col key={card.key} className='pb-4' xs={12} sm={6} md={4} lg={2}>
            <Card className='h-100'>
              <CardBody className='p-16'>
                <div className='text-center'>
                  <div className='h1'>{formattedNumber}</div>
                  <div>{card.label}</div>
                </div>
              </CardBody>
            </Card>
          </Col>
        ))}
      </Row>
    );
  }
}

export default withI18n()(Statistics);
