import useSWR from 'swr';

const useUserNotificationsCount = () => {
  const { data, mutate } = useSWR('/user/notifications_count/', {
    shouldRetryOnError: false,
    refreshInterval: 15000,
    refreshWhenHidden: true,
    fallbackData: { count: 0 },
  });

  return { data, mutate };
};

export default useUserNotificationsCount;
