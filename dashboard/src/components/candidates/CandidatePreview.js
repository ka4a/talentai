import React from 'react';

import _ from 'lodash';
import PropTypes from 'prop-types';
import classnames from 'classnames';
import { Trans } from '@lingui/macro';

import Avatar from '../UI/Avatar';
import Typography from '../UI/Typography';

function CurrentJob(props) {
  const { company, position } = props;

  let content;

  if (company && position) {
    content = (
      <Trans>
        {position} at {company}
      </Trans>
    );
  } else {
    content = (
      <>
        {company}
        {position}
      </>
    );
  }

  return (
    <Typography variant='h3'>
      <span style={{ color: '#6C9BF9' }}>{content}</span>
    </Typography>
  );
}

export default function CandidatePreview(props) {
  const { candidate, className } = props;

  return (
    <>
      <div className={classnames('d-flex justify-content-between', className)}>
        <div>
          <CurrentJob
            company={candidate.currentCompany}
            position={candidate.currentPosition}
          />

          <div className='text-muted'>
            <Typography>
              <>
                {candidate.email}
                {candidate.phone && (
                  <span>&nbsp;|&nbsp;{candidate.secondaryPhone}</span>
                )}
              </>
            </Typography>
          </div>
        </div>

        <span>
          <Avatar size='lg' shape='square' src={candidate.photo} />
        </span>
      </div>

      <div>
        {candidate.languages.length && (
          <div className='mb-24'>
            <div>
              <Typography variant='h3'>
                <Trans>Languages</Trans>
              </Typography>
            </div>
            {_.map(candidate.languages, (l) => l.formatted).join(', ')}
          </div>
        )}
      </div>
    </>
  );
}

CandidatePreview.propTypes = {
  candidate: PropTypes.object.isRequired,
};
