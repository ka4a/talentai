import { useCallback } from 'react';

import { v4 as uuid } from 'uuid';

export const useAddDynamicListRow = (setForm, name, rowTemplate) =>
  useCallback(() => {
    const newRow = { localId: uuid(), ...rowTemplate };

    setForm((oldForm) => ({
      ...oldForm,
      [name]: [...oldForm[name], newRow],
    }));
  }, [setForm, name, rowTemplate]);

export const useRemoveDynamicListRow = (setForm, name) =>
  useCallback(
    (event) => {
      const id = String(event.currentTarget.dataset.id);

      return setForm((oldForm) => ({
        ...oldForm,
        [name]: oldForm[name].filter((row) => id !== getRowId(row)),
      }));
    },
    [setForm, name]
  );

const getRowId = (row) => (row.id ? String(row.id) : row.localId);
