import { useCallback } from 'react';

import cloneDeep from 'lodash/cloneDeep';
import differenceBy from 'lodash/differenceBy';
import { useLingui } from '@lingui/react';

import { useGetJob, useProposalsRead } from '@swrAPI';
import { DECISION_CHOICES } from '@constants';
import { getChoiceName } from '@utils';
import { useTranslatedChoices } from '@hooks';

const useForm = (closeModal, interviewId) => {
  const { i18n } = useLingui();
  const decisionChoices = useTranslatedChoices(i18n, DECISION_CHOICES);

  const { data: job } = useGetJob();
  const { mutate: refreshProposal } = useProposalsRead();

  const processReadObject = useCallback((interview) => {
    const hiringCriteria = interview.assessment.hiringCriteriaAssessment.reduce(
      (acc, el) => {
        acc[el.hiringCriterionId] = el.rating;
        return acc;
      },
      {}
    );

    return { ...interview.assessment, hiringCriteria };
  }, []);

  const processFormState = useCallback(
    (form) => {
      const formCopy = cloneDeep(form);

      let hiringCriteriaAssessment = Object.entries(formCopy.hiringCriteria).reduce(
        (acc, [id, rating]) => {
          acc.push({ hiringCriterionId: id, rating });
          return acc;
        },
        []
      );

      // check not selected rating fields and add 'null' value to them
      const difference = differenceBy(
        job.hiringCriteria.map((el) => ({ ...el, hiringCriterionId: String(el.id) })),
        hiringCriteriaAssessment,
        'hiringCriterionId'
      );

      hiringCriteriaAssessment = hiringCriteriaAssessment.concat(
        difference.map(({ hiringCriterionId }) => ({
          hiringCriterionId,
          rating: null,
        }))
      );

      delete formCopy.hiringCriteria;

      return {
        ...formCopy,
        id: interviewId,
        hiringCriteriaAssessment,
        decisionDisplay: getChoiceName(decisionChoices, formCopy.decision),
      };
    },
    [interviewId, job.hiringCriteria, decisionChoices]
  );

  const onSaved = useCallback(async () => {
    closeModal();
    await refreshProposal();
  }, [closeModal, refreshProposal]);

  return {
    processReadObject,
    processFormState,
    onSaved,
  };
};

export default useForm;
