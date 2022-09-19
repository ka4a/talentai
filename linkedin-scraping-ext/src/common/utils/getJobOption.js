import toProposalPresetStr from './toProposalPresetStr';
import getProposalPresetTitleStr from './getProposalPresetTitleStr';

export default (job, listTitle, stage) => ({
  title: getProposalPresetTitleStr(job, listTitle),
  id: toProposalPresetStr(job.id, stage),
});
