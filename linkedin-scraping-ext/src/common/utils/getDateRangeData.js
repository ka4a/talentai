import moment from 'moment';
import 'moment/locale/ja';

const IN_FORMAT = ['l', 'MMM YYYY'];
const OUT_FORMAT = 'YYYY-MM-DD';
const PRESENT_WORD = {
  ja: '現在',
  en: 'Present',
};

function format(dateStr, locale) {
  const date = moment(dateStr, IN_FORMAT, locale);
  return date.isValid() ? date.format(OUT_FORMAT) : null;
}

export default function getDateRangeData(range, lang) {
  const [start, end] = range.split(' – ');
  const currentlyPursuing = end === PRESENT_WORD[lang];
  return {
    currentlyPursuing,
    dateStart: format(start, lang),
    dateEnd: currentlyPursuing ? null : format(end, lang),
  };
}
