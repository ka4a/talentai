import React from 'react';

import PropTypes from 'prop-types';
import { defineMessage } from '@lingui/macro';
import { useLingui } from '@lingui/react';

import { Loading, DefaultPageContainer } from '@components';
import { useLegalAgreementsRead } from '@swrAPI';

function LegalAgreementFilePage({ match }) {
  const { type } = match.params;

  const typeData = TYPE_MAP[type];

  const { data, error } = useLegalAgreementsRead(typeData?.id);
  const { i18n } = useLingui();

  if (error || !typeData) {
    // Not found function would be displayed at upper level
    return null;
  }

  if (data) {
    window.location.href = data.file;
    return null;
  }

  return (
    <DefaultPageContainer
      title={i18n._(typeData.title)}
      colAttrs={{ xs: 12, md: { size: 8, offset: 2 } }}
    >
      <Loading />
    </DefaultPageContainer>
  );
}

const TYPE_MAP = {
  privacy: {
    id: 'pp',
    title: defineMessage({ message: 'Privacy Policy' }).id,
  },
  terms: {
    id: 'tandc',
    title: defineMessage({ message: 'Terms & Conditions' }).id,
  },
};

LegalAgreementFilePage.propTypes = {
  match: PropTypes.shape({
    params: PropTypes.shape({
      type: PropTypes.oneOf(Object.keys(TYPE_MAP)),
    }),
  }).isRequired,
};

export default LegalAgreementFilePage;
