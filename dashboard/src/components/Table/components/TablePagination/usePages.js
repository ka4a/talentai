import range from 'lodash/range';

const usePages = ({
  offset,
  limit,
  count,
  pageRangeDisplayed,
  marginPagesDisplayed,
}) => {
  const currentPage = Math.trunc(offset / limit) + 1;
  const maxPage = Math.ceil(count / limit);

  // Maximum of pages that can be displayed on the middle range to each side
  const maxLeftFromCenter = Math.ceil(pageRangeDisplayed / 2) - 1;
  const maxRightFromCenter = Math.floor(pageRangeDisplayed / 2);

  // Calculating pages of the middle range
  const firstPageOfMiddleRange = Math.max(1, currentPage - maxLeftFromCenter);
  const lastPageOfMiddleRange = Math.min(maxPage, currentPage + maxRightFromCenter);

  // Insert ... between middle range and first and last pages
  const isEllipsisOnLeft = firstPageOfMiddleRange - 1 > marginPagesDisplayed;
  const isEllipsisOnRight =
    lastPageOfMiddleRange + 1 < maxPage - marginPagesDisplayed + 1;

  const lastPageOfLeftMargin = isEllipsisOnLeft
    ? marginPagesDisplayed
    : firstPageOfMiddleRange - 1;
  const firstPageOfRightMargin = isEllipsisOnRight
    ? maxPage - marginPagesDisplayed + 1
    : lastPageOfMiddleRange + 1;

  const pageFirstItemNumber = limit * (currentPage - 1) + 1;
  const pageLastItemNumber = Math.min(limit * currentPage, count);

  const pages = [];

  if (lastPageOfLeftMargin >= 1) {
    pages.push(...range(1, lastPageOfLeftMargin + 1));
  }

  if (isEllipsisOnLeft) {
    pages.push(-1); // -1 - for left ellipsis
  }

  if (lastPageOfMiddleRange >= firstPageOfMiddleRange) {
    pages.push(...range(firstPageOfMiddleRange, lastPageOfMiddleRange + 1));
  }

  if (isEllipsisOnRight) {
    // -2 - for right ellipsis (different -1 and -2 are used to keep keys unique)
    pages.push(-2);
  }

  if (maxPage >= firstPageOfRightMargin) {
    pages.push(...range(firstPageOfRightMargin, maxPage + 1));
  }

  return { pages, pageFirstItemNumber, pageLastItemNumber, currentPage, maxPage };
};

export default usePages;
