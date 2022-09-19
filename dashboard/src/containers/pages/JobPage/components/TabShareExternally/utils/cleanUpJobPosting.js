export default function cleanUpJobPosting(jobPosting) {
  if (!jobPosting) return jobPosting;
  return {
    ...jobPosting,
    // We receive salaryFrom and salaryTo fields as null
    // To prevent it from showing up we do this cleanup
    salaryFrom: jobPosting.salaryFrom ?? '',
    salaryTo: jobPosting.salaryTo ?? '',
  };
}
