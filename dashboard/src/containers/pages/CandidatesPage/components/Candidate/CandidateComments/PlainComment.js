import React from 'react';
import { Link } from 'react-router-dom';

import { Trans } from '@lingui/macro';

import HumanizedDate from '@components/format/HumanizedDate';

import styles from './PlainComment.module.scss';

const DAY = 1000 * 60 * 60 * 24;

const PlainComment = ({ comment, onDelete, user, getCommentAuthor }) => {
  const re = /@\[([\s\w]+)\]\((\d+)\)/g;
  const matches = comment.text.matchAll(re);
  let text = comment.text;
  for (var match of matches) {
    text = text.replaceAll(
      match[0],
      `<span class='${styles.userBadge} ${
        user.id === parseInt(match[2]) ? styles.currentUser : ''
      }'>${match[1]}</span>`
    );
  }
  return (
    <div key={comment.id}>
      {comment.author ? <b>{getCommentAuthor(comment.author)}:</b> : ''}{' '}
      <span
        className={styles.multiLineComment}
        dangerouslySetInnerHTML={{ __html: text }}
      />
      <br />
      <small className='text-muted'>
        <HumanizedDate date={comment.createdAt} threshold={DAY} />
      </small>
      {user.id === comment.author.id ? (
        <>
          &nbsp;&middot;&nbsp;
          <small>
            <Link onClick={() => onDelete(comment.id)}>
              <Trans>Delete</Trans>
            </Link>
          </small>
        </>
      ) : null}
      <hr />
    </div>
  );
};

export default PlainComment;
