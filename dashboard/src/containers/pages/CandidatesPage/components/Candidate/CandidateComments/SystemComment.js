import React from 'react';

import HumanizedDate from '@components/format/HumanizedDate';

const DAY = 1000 * 60 * 60 * 24;

const SystemComment = ({ comment, getCommentAuthor }) => {
  const author = getCommentAuthor(comment.author);

  return (
    <div>
      {comment.candidate !== undefined ? (
        <div>
          {comment.text} by <b>{author}</b>
        </div>
      ) : (
        <div>
          Candidate was{' '}
          <span style={{ textTransform: 'lowercase' }}>{comment.text}</span> by{' '}
          <b>{author}</b> on{' '}
          <b>
            {comment.proposal.company} - {comment.proposal.jobName}
          </b>
        </div>
      )}
      <div>
        <small className='text-muted'>
          <HumanizedDate date={comment.createdAt} threshold={DAY} />
        </small>
      </div>
      <hr />
    </div>
  );
};

export default SystemComment;
