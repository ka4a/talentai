import useStaffList from './useStaffList';

const useStaffOptions = () => {
  const swr = useStaffList();
  if (!swr.data) return [];

  return swr.data.results.map((user) => ({
    value: user.id,
    name: `${user.firstName} ${user.lastName}`,
  }));
};

export default useStaffOptions;
