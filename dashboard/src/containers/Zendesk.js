import React, { memo, useCallback, useEffect, useState } from 'react';
import ReactZendesk, { ZendeskAPI } from 'react-zendesk';
import { useSelector } from 'react-redux';

import { t } from '@lingui/macro';

import { showSuccessToast } from '@utils';
import { client } from '@client';

import store from '../store';

const key = process.env.REACT_APP_ZENDESK_WIDGET_KEY;

const settings = {
  zendeskKey: key,
  webWidget: {
    contactForm: {
      subject: true,
      attachments: false,
    },
    position: { horizontal: 'right', vertical: 'top' },
    chat: { suppress: true },
    talk: { suppress: true },
    answerBot: { suppress: true },
    helpCenter: { suppress: true },
  },
};

const isProduction = process.env.NODE_ENV === 'production';

const Zendesk = () => {
  const [isLoaded, setIsLoaded] = useState(false);
  const locale = useSelector((state) => state.settings.locale);

  const { isAuthenticated, firstName, lastName, email, profile } = useSelector(
    (state) => state.user
  );

  useEffect(() => {
    if (isProduction && !isAuthenticated) ZendeskAPI('webWidget', 'logout');
  }, [isAuthenticated]);

  useEffect(() => {
    if (!isLoaded) return;
    ZendeskAPI('webWidget', 'setLocale', locale);
  }, [isLoaded, locale]);

  const orgName = profile?.org?.name;

  useEffect(() => {
    if (isLoaded && isAuthenticated) {
      ZendeskAPI('webWidget', 'prefill', {
        name: {
          value: `${firstName} ${lastName}`,
          readOnly: Boolean(firstName && lastName),
        },
        email: { value: email, readOnly: Boolean(email) },
      });

      if (isProduction) {
        ZendeskAPI('webWidget', 'identify', {
          name: `${firstName} ${lastName}`,
          organization: orgName,
          email,
        });
      }
    }
  }, [email, firstName, isAuthenticated, isLoaded, lastName, orgName]);

  const onLoaded = useCallback(() => {
    setIsLoaded(true);

    // hide launcher button when loaded
    ZendeskAPI('webWidget', 'hide');

    // hide launcher button when form is closed
    ZendeskAPI('webWidget:on', 'close', () => {
      ZendeskAPI('webWidget', 'hide');
    });

    ZendeskAPI('webWidget:on', 'userEvent', async (event) => {
      if (event.action === 'Contact Form Submitted') {
        await sendFeedback();
      }
    });
  }, [setIsLoaded]);

  return key && <ReactZendesk {...settings} onLoaded={onLoaded} />;
};

async function sendFeedback() {
  try {
    await client.execute({
      operationId: 'feedback_create',
      parameters: {
        data: {
          reduxState: store.getState(),
          pageUrl: window.location.pathname,
          pageHtml: document.documentElement.outerHTML,
          text: 'Zendesk',
        },
      },
    });

    showSuccessToast(t`Sent Successfully! Support will contact you shortly.`);
  } catch {
    // empty
  }
}

export default memo(Zendesk);
