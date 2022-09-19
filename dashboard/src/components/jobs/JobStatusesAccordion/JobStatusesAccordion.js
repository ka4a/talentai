import React, { memo, useEffect } from 'react';
import { CardBody, Card } from 'reactstrap';
import { useToggle } from 'react-use';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { Trans } from '@lingui/macro';

import Avatar from '../../UI/Avatar';
import Typography from '../../UI/Typography';
import Collapse from '../../Collapse';

import styles from './JobStatusesAccordion.module.scss';

const JobStatusesAccordion = (props) => {
  const {
    title,
    items,
    titleClassname,
    activeItemId,
    setActiveItem,
    content,
    disabled,
    count,
    totalCount,
    isOpen: isOpenSource,
  } = props;

  const [isOpen, toggle] = useToggle(isOpenSource && !disabled);

  useEffect(() => {
    if (isOpenSource) toggle(isOpenSource);
  }, [isOpenSource, toggle]);

  const displayedCount = totalCount ? `${count}/${totalCount}` : count;

  return (
    <div
      className={classnames([
        styles.container,
        { [styles.opened]: isOpen && !disabled },
      ])}
    >
      <Collapse
        isOpen={isOpen}
        toggle={toggle}
        title={
          <Typography
            variant='h3'
            className={classnames(styles.title, {
              [styles.disabled]: disabled,
              [styles[titleClassname]]: titleClassname,
            })}
          >
            <Trans id={title} /> ({displayedCount})
          </Typography>
        }
        isDisabled={disabled}
      >
        {content || (
          <div className={styles.cardsWrapper}>
            {items.map((item) => (
              <Card
                key={item.id}
                className={classnames(styles.cardWrap, {
                  [styles.active]: activeItemId === item.id,
                })}
                onClick={() => setActiveItem(item.id)}
              >
                <CardBody className={styles.card}>
                  <div className={styles.itemRow}>
                    <div className={styles.nameWrapper}>
                      <Avatar shape='circle' />

                      <Typography className={styles.name}>{item.name}</Typography>
                    </div>

                    <Typography variant='caption'>{item.agency}</Typography>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        )}
      </Collapse>
    </div>
  );
};

JobStatusesAccordion.propTypes = {
  title: PropTypes.string,
  count: PropTypes.number,
  totalCount: PropTypes.number,
  titleClassname: PropTypes.string,
  activeItemId: PropTypes.number,
  setActiveItem: PropTypes.func,
  defaultOpen: PropTypes.bool,
  disabled: PropTypes.bool,
  items: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      name: PropTypes.string,
      agency: PropTypes.string,
    })
  ),
};

export default memo(JobStatusesAccordion);
