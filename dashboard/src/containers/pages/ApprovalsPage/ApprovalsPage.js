import React, { memo } from 'react';
import { Nav, NavItem, NavLink } from 'reactstrap';
import { useRouteMatch } from 'react-router';

import { compose } from 'redux';
import { t, Trans } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import { DefaultPageContainer } from '@components';

import FeeApprovalsTable from '../../../components/fee/FeeApprovalsTable/FeeApprovalsTable';
import { TableHeader } from '../../../components/SwaggerTable';

import styles from './ApprovalsPage.module.scss';

ApprovalsPage.propTypes = {};

const PATHS = {
  fee: '/a/approvals/fees',
  placement: '/a/approvals/placements',
  proposal: '/a/approvals/proposals',
};

const wrapper = compose(memo, withI18n());

function ApprovalsPage(props) {
  const { i18n } = props;

  const feeMatch = useRouteMatch(PATHS.fee);
  const placementMatch = useRouteMatch(PATHS.placement);
  const proposalMatch = useRouteMatch(PATHS.proposal);

  let feeApprovalType = null;
  if (feeMatch) feeApprovalType = 'fee';
  else if (placementMatch) feeApprovalType = 'placement';
  else if (proposalMatch) feeApprovalType = 'proposal';

  const title = i18n._(t`Approvals`);

  return (
    <>
      <DefaultPageContainer title={title} colAttrs={{ xs: 12 }}>
        <TableHeader title={title} />
        <Nav tabs className={styles.navBar}>
          <NavItem>
            <NavLink href={PATHS.fee} active={feeMatch != null}>
              <Trans>Fees</Trans>
            </NavLink>
          </NavItem>
          <NavItem>
            <NavLink href={PATHS.placement} active={placementMatch != null}>
              <Trans>Placements</Trans>
            </NavLink>
          </NavItem>
          <NavItem>
            <NavLink href={PATHS.proposal} active={proposalMatch != null}>
              <Trans>Proposals</Trans>
            </NavLink>
          </NavItem>
        </Nav>
        {feeApprovalType ? (
          <FeeApprovalsTable type={feeApprovalType} baseUrl={PATHS[feeApprovalType]} />
        ) : null}
      </DefaultPageContainer>
    </>
  );
}

export default wrapper(ApprovalsPage);
