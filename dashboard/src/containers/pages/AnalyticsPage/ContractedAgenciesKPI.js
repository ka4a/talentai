import React from 'react';
import { Link } from 'react-router-dom';

import { useLingui } from '@lingui/react';
import { t } from '@lingui/macro';

import { Loading } from '@components/UI/Loading';

import AnalyticsBlock from './AnalyticsBlock';
import { useSwagger } from '../../../hooks';
import ErrorPlaceholder from './ErrorPlaceholder';

export default function ContractedAgenciesKPI() {
  const { obj: data, loading, error } = useSwagger('stats_contracts');
  const { i18n } = useLingui();

  return (
    <AnalyticsBlock
      title={i18n._(t`Contracted Agencies`)}
      titleSizeSm
      size={3}
      height='120px'
    >
      {loading && <Loading />}
      {!loading && error && <ErrorPlaceholder />}
      {data && !loading && (
        <>
          <Link to='/c/agencies' className='text-primary fs-24 font-weight-bold'>
            {data.contracts}
          </Link>
        </>
      )}
    </AnalyticsBlock>
  );
}
