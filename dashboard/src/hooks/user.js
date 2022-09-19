import { useSelector } from 'react-redux';

import { getCareerSiteUrl } from '@utils';

export function useCareerSiteUrl() {
  const slug = useSelector(({ user }) => user?.profile.org.careerSiteSlug);
  return getCareerSiteUrl(slug);
}
