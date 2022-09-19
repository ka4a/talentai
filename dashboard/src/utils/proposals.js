export function formatStageLabel(label, orgType) {
  const [clientLabel, agencyLabel] = label.split('//');
  return agencyLabel && orgType !== 'client' ? agencyLabel : clientLabel;
}
