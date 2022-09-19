import axios from 'axios';

const fetcher = async (url, options) => {
  const response = await axios.get(url, {
    baseURL: '/api',
    ...options,
  });
  return response.data;
};

export default fetcher;
