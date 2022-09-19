// Used to translate choice labels after translation framework is initialized
export const translateChoices = (i18n, choices, labelField = 'name') =>
  choices.map((choice) => ({
    ...choice,
    [labelField]: i18n._(choice[labelField]),
  }));

export function getLocalizedField(item, field, locale, fallback = '') {
  if (locale === 'ja') field = `${field}Ja`;
  return item?.[field] ?? '';
}

export function translateMap(i18n, map) {
  const translatedMap = {};

  for (let [field, value] of Object.entries(map)) {
    translatedMap[field] = i18n._(value);
  }

  return translatedMap;
}
