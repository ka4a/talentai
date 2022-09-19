import React from 'react';

import PropTypes from 'prop-types';

import HumanizedDate from '@components/format/HumanizedDate';

import UserInline from '../../../../../components/UserInline';

import styles from './ProposalComment.module.scss';

const getCommentAuthor = (author) => {
  if (typeof author === 'object') {
    return <UserInline user={author} />;
  }
  return author;
};

const SystemComment = ({ comment }) => (
  <div key={comment.id}>
    {comment.text} by <b>{getCommentAuthor(comment.author)}</b>
    <br />
    <small className='text-muted'>
      <HumanizedDate date={comment.createdAt} />
    </small>
    <hr />
  </div>
);

const PlainComment = ({ comment }) => (
  <div key={comment.id}>
    {comment.author ? <b>{getCommentAuthor(comment.author)}:</b> : ''}{' '}
    <span className={styles.multiLineComment}>{comment.text}</span>
    <br />
    <small className='text-muted'>
      <HumanizedDate date={comment.createdAt} />
    </small>
    <hr />
  </div>
);

export default class ProposalComment extends React.Component {
  render() {
    const { comments } = this.props;

    return (
      <div className='pt-16 pl-4'>
        {comments.map((comment) => {
          return comment.system ? (
            <SystemComment key={comment.id} comment={comment} />
          ) : (
            <PlainComment key={comment.id} comment={comment} />
          );
        })}
      </div>
    );
  }
}

ProposalComment.propTypes = {
  comments: PropTypes.array.isRequired,
};
