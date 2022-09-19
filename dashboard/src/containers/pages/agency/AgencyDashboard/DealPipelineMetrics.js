import React, { memo } from 'react';
import { Card, CardBody, Col, Row } from 'reactstrap';

import _ from 'lodash';
import { t } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { useSwagger, useToggle } from '../../../../hooks';
import DealPipelineCandidatesModal from './DealPipelineCandidatesModal';

const COLUMNS = [
  { key: 'firstRound', name: t`First stage` },
  { key: 'intermediateRound', name: t`Intermediate stage` },
  { key: 'finalRound', name: t`Final stage` },
  { key: 'offerRound', name: t`Offer stage` },
  { key: 'total', name: t`Total` },
];

const ROWS = [
  { key: 'total', name: t`Total` },
  { key: 'realistic', name: t`Realistic` },
];

function DealPipelineMetrics({ className, shortlistedBy }) {
  const { obj: data, errorObj } = useSwagger('get_deal_pipeline_metrics', {
    shortlisted_by: shortlistedBy,
  });
  const switcher = useToggle();

  const { i18n } = useLingui();

  if (!data || errorObj) {
    return null;
  }

  return (
    <>
      <DealPipelineCandidatesModal
        isOpen={switcher.value}
        toggle={switcher.toggle}
        stageFilter={switcher.params}
      />

      <div className={className}>
        <Row className='mb-3 mr-0'>
          <Col xs={12} sm={6} md={4} lg={2} />

          {_.map(COLUMNS, (column) => (
            <Col
              className='d-inline-flex justify-content-center'
              key={column.value}
              xs={12}
              sm={6}
              md={4}
              lg={2}
            >
              <span className='text-secondary'>{column.name}</span>
            </Col>
          ))}
        </Row>

        {_.map(ROWS, (row) => (
          <Row key={row.value} className='mb-3 mr-0'>
            <Col
              className='d-inline-flex justify-content-center align-items-center'
              xs={12}
              sm={6}
              md={4}
              lg={2}
            >
              <span className='text-secondary'>{row.name}</span>
            </Col>

            {_.map(_.keys(data[row.key]), (round) => (
              <Col key={`${row.key}${round}`} xs={12} sm={6} md={4} lg={2}>
                <Card
                  onClick={(e) => switcher.toggle(e, round)}
                  style={{ cursor: 'pointer' }}
                >
                  <CardBody>
                    <div className='text-center'>
                      <div className='h3'>{i18n.number(data?.[row.key]?.round)}</div>
                    </div>
                  </CardBody>
                </Card>
              </Col>
            ))}
          </Row>
        ))}
      </div>
    </>
  );
}

export default memo(DealPipelineMetrics);
