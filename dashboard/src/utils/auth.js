import intersection from 'lodash/intersection';

export const isUserBelongToGroups = (user, groups) => {
  return (
    user.isAuthenticated &&
    (groups === null || intersection(user.groups, groups).length > 0)
  );
};
