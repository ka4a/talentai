import React, { Fragment } from 'react';

import PropTypes from 'prop-types';

import { ReactComponent as TrashCan } from '@images/icons/trash-can.svg';

import Button from '../Button';
import Typography from '../Typography';

import styles from './DynamicList.module.scss';

const DynamicList = (props) => {
  const {
    title,
    data,
    fields: sourceFields,
    addRowText,
    onAddRow,
    onRemoveRow,
    isDeleteShown,
  } = props;

  return (
    <div>
      {Boolean(title) && (
        <Typography className={styles.title} variant='subheading'>
          {title}
        </Typography>
      )}

      {data.map((el, idx) => {
        const fields =
          typeof sourceFields === 'function' ? sourceFields(idx) : sourceFields;

        return (
          <div className={styles.row} key={el.id ?? el.localId}>
            {fields.map((field) => (
              <Fragment key={field.id}>{field.render(idx, el)}</Fragment>
            ))}

            {isDeleteShown && (
              <TrashCan
                data-id={el.id ?? el.localId}
                className={styles.delete}
                onClick={onRemoveRow}
              />
            )}
          </div>
        );
      })}

      <Button className={styles.addButton} variant='text' onClick={onAddRow}>
        {addRowText}
      </Button>
    </div>
  );
};

DynamicList.propTypes = {
  title: PropTypes.string,
  data: PropTypes.arrayOf(PropTypes.object),
  fields: PropTypes.oneOfType([
    PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number,
        render: PropTypes.func,
      })
    ),
    PropTypes.func,
  ]).isRequired,
  addRowText: PropTypes.string.isRequired,
  onAddRow: PropTypes.func.isRequired,
  onRemoveRow: PropTypes.func,
  isDeleteShown: PropTypes.bool,
};

DynamicList.defaultProps = {
  title: null,
  isDeleteShown: true,
  onRemoveRow: () => {},
  data: [],
};

export default DynamicList;
