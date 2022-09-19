import React from 'react';
import { Button, FormGroup, Nav, NavItem, NavLink } from 'reactstrap';
import { connect } from 'react-redux';

import autosize from 'autosize';
import classnames from 'classnames';
import PropTypes from 'prop-types';
import _ from 'lodash';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import { AGENCY_GROUPS, CLIENT_GROUPS } from '@constants';

import SwaggerForm from '../../../../components/SwaggerForm';
import ProposalComment from './ProposalComment';

const mapStateToProps = (state) => ({
  user: state.user,
});

class ProposalComments extends React.Component {
  toggleTabs = (value) => {
    if (this.props.commentsParams.publicTab !== value) {
      this.props.onChange({
        publicTab: value,
        limit: 10,
      });
    }
  };

  onLoadMore = () => {
    const { commentsParams } = this.props;

    this.props.onChange({
      ...commentsParams,
      limit: commentsParams.limit + 10,
    });
  };

  getTabName = (isPublic) => {
    const { proposal } = this.props;

    if (_.intersection(this.props.user.groups, CLIENT_GROUPS).length > 0) {
      return isPublic ? proposal.clientName : proposal.source.name;
    } else if (_.intersection(this.props.user.groups, AGENCY_GROUPS).length > 0) {
      return isPublic ? proposal.source.name : proposal.clientName;
    }

    return isPublic ? 'Own' : 'Other';
  };

  getInputs = ({ FormInput }) => (
    <div>
      <FormGroup>
        <FormInput
          type='textarea'
          label={this.props.i18n._(t`New Comment`)}
          onKeyUp={(e) => {
            autosize(e.target);
          }}
          name='text'
          rows={2}
        />
      </FormGroup>
    </div>
  );

  getButtons = (form, onSubmit, defaultButtonAttrs) => (
    <div className='text-right'>
      <Button {...defaultButtonAttrs} color='secondary-blue'>
        <Trans>Add comment</Trans>
      </Button>
    </div>
  );

  render() {
    const {
      proposal,
      commentsParams: { publicTab, limit },
      commentsData: { count, comments },
    } = this.props;

    return (
      <>
        <Nav tabs>
          <NavItem>
            <NavLink
              className={classnames({ active: !publicTab })}
              onClick={() => {
                this.toggleTabs(false);
              }}
            >
              {this.getTabName(true)} <Trans>Activity</Trans>
            </NavLink>
          </NavItem>
          {proposal.source.organizationType === 'agency' ? (
            <NavItem>
              <NavLink
                className={classnames({ active: publicTab })}
                onClick={() => {
                  this.toggleTabs(true);
                }}
              >
                {this.getTabName(false)} <Trans>Activity</Trans>
              </NavLink>
            </NavItem>
          ) : null}
        </Nav>

        {limit < count ? (
          <Button color='link' onClick={this.onLoadMore}>
            <Trans>Load more</Trans>
          </Button>
        ) : null}

        <ProposalComment comments={comments} />

        <SwaggerForm
          formId='proposalCommentModalForm'
          operationId='proposal_comment_create'
          onSaved={() => this.props.onChange()}
          closeOnSaved={false}
          resetAfterSave={true}
          handlers={this.props.handlers}
          initialState={{ text: '', proposal: proposal.id }}
          defaultSubmitData={{ public: publicTab }}
          inputs={this.getInputs}
          buttons={this.getButtons}
        />
      </>
    );
  }
}

ProposalComments.propTypes = {
  proposal: PropTypes.object.isRequired,
  commentsParams: PropTypes.object.isRequired,
  commentsData: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default connect(mapStateToProps)(withI18n()(ProposalComments));
