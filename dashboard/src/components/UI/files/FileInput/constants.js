const IMAGE_TYPES = ['.jpeg', '.jpg', '.png', '.gif'];
const RESUME_TYPES = ['.pdf', '.doc', '.docx', '.xlsx', '.xls', '.txt', '.odt', '.rtf'];

export const OTHER_FILES_TYPES = [...IMAGE_TYPES, ...RESUME_TYPES, '.ppt', '.pptx'];
export const FILE_TYPES = {
  image: IMAGE_TYPES,
  resume: RESUME_TYPES,
};
