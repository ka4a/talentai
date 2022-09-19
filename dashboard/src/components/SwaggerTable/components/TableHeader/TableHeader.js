import React, { memo } from 'react';
import { Container, Row, Col } from 'reactstrap';

import PropTypes from 'prop-types';
import classNames from 'classnames';

import Typography from '../../../UI/Typography';
import SearchInput from '../../../UI/SearchInput';

import styles from './TableHeader.module.scss';

const TableHeader = (props) => {
  const {
    title,
    search = false,
    onlySearch = false,
    onlySearchWithRightSide = false,
    searchInputClassName,
    leftSide,
    rightSide,
    state,
    setState,
    filtersBar,
  } = props;

  if (onlySearch) {
    return (
      <div
        className={classNames(
          onlySearchWithRightSide ? styles.searchWrapper : styles.bottomGap
        )}
      >
        <Container className={styles.searchContentWrapper}>
          <SearchInput
            className={searchInputClassName}
            state={state}
            setState={setState}
            mode='form'
          />
          {onlySearchWithRightSide && rightSide}
        </Container>
      </div>
    );
  }

  return (
    <div className={styles.headerWrapper}>
      <Container>
        <Row className='mb-16'>
          <Col className='align-items-center'>
            <Typography variant='h1'>
              {typeof title === 'function' ? title(state) : title}
            </Typography>
            {leftSide}
          </Col>

          <Col className='text-right align-self-center'>{rightSide}</Col>
        </Row>

        <Row>
          {search && (
            <Col lg={2} className={styles.search}>
              <SearchInput
                className={searchInputClassName}
                state={state}
                setState={setState}
                mode='form'
              />
            </Col>
          )}
          <Col className='align-self-center'>{filtersBar}</Col>
        </Row>
      </Container>
    </div>
  );
};

TableHeader.propTypes = {
  title: PropTypes.oneOfType([PropTypes.node, PropTypes.func]),
  search: PropTypes.bool,
  onlySearch: PropTypes.bool,
  searchInputClassName: PropTypes.string,
  rightSide: PropTypes.node,
  state: PropTypes.object.isRequired,
  setState: PropTypes.func.isRequired,
  leftSide: PropTypes.node,
};

export default memo(TableHeader);
