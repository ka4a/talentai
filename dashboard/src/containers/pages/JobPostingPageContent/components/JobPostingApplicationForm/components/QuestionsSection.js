import React from 'react';

import { t, Trans } from '@lingui/macro';
import PropTypes from 'prop-types';

import { Typography } from '@components';

import styles from './Sections.module.scss';

const QuestionsSection = ({ questions, FormInput }) => (
  <>
    <Typography variant='subheading'>
      <Trans>Questions</Trans>
    </Typography>

    <div className={styles.topGap}>
      {questions.map((el, index) => (
        <div key={el.id} className={styles.questionWrapper}>
          <Typography className={styles.question}>{el.question}</Typography>

          <FormInput
            label={t`Answer`}
            type='rich-editor'
            name={`questions[${index}].answer`}
            required
          />
        </div>
      ))}
    </div>

    <hr />
  </>
);

QuestionsSection.propTypes = {
  questions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      question: PropTypes.string,
      answer: PropTypes.string,
    })
  ).isRequired,
  FormInput: PropTypes.func.isRequired,
};

export default QuestionsSection;
