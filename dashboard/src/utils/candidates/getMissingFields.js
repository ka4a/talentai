import { t } from '@lingui/macro';

const fieldsBeingChecked = [
  { key: 'email', title: t`Email (Primary)` },
  { key: 'currentPosition', title: t`Current Job Title` },
  { key: 'currentCompany', title: t`Current Company` },
  { key: 'currentSalary', title: t`Current Annual Fixed` },
  { key: 'source', title: t`Source` },
  { key: 'owner', title: t`Sourced By` },
];

const getMissingFields = ({ form, withLanguages = true }) => {
  const emptyFields = [];

  fieldsBeingChecked.forEach((el) => {
    if (!form[el.key]) emptyFields.push(el.title);
  });

  if (withLanguages) {
    if (form.languages.length === 0) emptyFields.push(t`Languages`);
  }

  if (form.allResume.length === 0) emptyFields.push(t`Resume`);

  return emptyFields;
};

export default getMissingFields;
