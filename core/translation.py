from modeltranslation.translator import register, TranslationOptions

from core import models as m

LANGUAGES = ('en', 'ja')


@register(m.ProposalStatus)
class ProposalStatusTranslationOptions(TranslationOptions):
    fields = ('status',)
    fallback_languages = {'default': LANGUAGES}


@register(m.ProposalComment)
class ProposalCommentTranslationOptions(TranslationOptions):
    fields = ('text',)
    fallback_languages = {'default': LANGUAGES}


@register(m.AgencyCategory)
class AgencyCategoryTranslationOptions(TranslationOptions):
    fields = ('title',)
    fallback_languages = {'default': LANGUAGES}


@register(m.ReasonDeclineCandidateOption)
class ReasonDeclineCandidateOptionOptions(TranslationOptions):
    fields = ('text',)
    fallback_languages = {'default': LANGUAGES}


@register(m.ReasonNotInterestedCandidateOption)
class ReasonNotInterestedCandidateOption(TranslationOptions):
    fields = ('text',)
    fallback_languages = {'default': LANGUAGES}


@register(m.Function)
class FunctionTranslationOptions(TranslationOptions):
    fields = ('title',)
    fallback_languages = {'default': LANGUAGES}
