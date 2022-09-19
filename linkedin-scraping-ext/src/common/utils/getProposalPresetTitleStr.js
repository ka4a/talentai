export default (job, listTitle) => {
  const { title, company } = job;
  const company__ = company ? `${company} - ` : '';
  return `${company__}${title} - ${listTitle}`;
};
