import React from 'react';

import PropTypes from 'prop-types';

import { UserInline } from '@components';

import SystemComment from './SystemComment';
import PlainComment from './PlainComment';

const getCommentAuthor = (author) => {
  if (typeof author === 'object') {
    return <UserInline user={author} />;
  }
  return author;
};

export default class CandidateComment extends React.Component {
  render() {
    const { comments, onDelete, user } = this.props;

    return (
      <div className='pt-16 pl-4'>
        {comments.map((comment) => {
          return comment.system ? (
            <SystemComment
              key={comment.id}
              comment={comment}
              getCommentAuthor={getCommentAuthor}
            />
          ) : (
            <PlainComment
              key={comment.id}
              comment={comment}
              user={user}
              onDelete={onDelete}
              getCommentAuthor={getCommentAuthor}
            />
          );
        })}
      </div>
    );
  }
}

CandidateComment.propTypes = {
  comments: PropTypes.array.isRequired,
  onDelete: PropTypes.func.isRequired,
  user: PropTypes.object.isRequired,
};
