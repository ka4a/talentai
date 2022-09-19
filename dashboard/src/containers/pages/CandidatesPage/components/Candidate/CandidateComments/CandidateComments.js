import React from 'react';
import { Button, FormGroup, Label } from 'reactstrap';
import { connect } from 'react-redux';
import { MentionsInput, Mention } from 'react-mentions';

import autosize from 'autosize';
import PropTypes from 'prop-types';
import _ from 'lodash';
import { compose } from 'redux';
import { withI18n } from '@lingui/react';
import { Trans } from '@lingui/macro';

import { client } from '@client';
import { SwaggerForm, Avatar } from '@components';

import CandidateComment from './CandidateComment';

import './CandidateComments.scss';

const mapStateToProps = (state) => ({
  user: state.user,
});

class CandidateComments extends React.Component {
  state = {
    staffList: [],
  };

  handleChange = () => {
    this.props.onChange();
  };

  onLoadMore = () => {
    const { commentsParams } = this.props;

    this.props.onChange({
      ...commentsParams,
      limit: commentsParams.limit + 5,
    });
  };

  onDelete = (commentId) => {
    this.props.onDelete({ id: commentId });
  };

  getInputs = ({ setValue, form }) => (
    <div>
      <FormGroup>
        <Label>
          <Trans>New Comment</Trans>
        </Label>
        <MentionsInput
          value={form.text || ''}
          onChange={(ev, value) => {
            autosize(ev.target);
            setValue('text', value);
          }}
          name='text'
          className='candidateCommentsMentions'
        >
          <Mention
            trigger='@'
            data={this.state.staffList}
            renderSuggestion={(suggestion, _, highlightedDisplay) => (
              <div className='d-flex flex-row'>
                <Avatar src={suggestion.photo} />
                <div className='pl-8 text-dark'>{highlightedDisplay}</div>
              </div>
            )}
            className='inputMention'
            appendSpaceOnAdd
            displayTransform={(id, display) => ` ${display} `}
          />
        </MentionsInput>
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

  fetchStaffList = () => {
    client
      .execute({
        operationId: 'staff_avatar_list',
        parameters: { count: 1000 },
      })
      .then((response) => {
        this.setState({
          staffList: _.map(response.obj.results, (obj) => ({
            id: obj.id,
            display: `${obj.firstName} ${obj.lastName}`,
            photo: obj.photo,
            firstName: obj.firstName,
            lastName: obj.lastName,
          })),
        });
      });
  };

  componentDidMount() {
    this.fetchStaffList();
  }
  render() {
    const { candidate, handlers, user } = this.props;
    const { limit } = this.props.commentsParams;
    const { count, comments } = this.props.commentsData;

    return (
      <>
        {limit < count ? (
          <Button color='link' onClick={this.onLoadMore}>
            <Trans>Load more</Trans>
          </Button>
        ) : null}

        <CandidateComment comments={comments} onDelete={this.onDelete} user={user} />

        <SwaggerForm
          formId='candidateCommentModalForm'
          operationId='candidate_comment_create'
          onSaved={this.handleChange}
          closeOnSaved={false}
          resetAfterSave={true}
          handlers={handlers}
          initialState={{ text: '', candidate: candidate.id }}
          inputs={this.getInputs}
          buttons={this.getButtons}
        />
      </>
    );
  }
}

CandidateComments.propTypes = {
  candidate: PropTypes.object.isRequired,
  commentsParams: PropTypes.object.isRequired,
  commentsData: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

const wrapper = compose(connect(mapStateToProps), withI18n());

export default wrapper(CandidateComments);
