import logging

from django.http import HttpResponseBadRequest, Http404
from django.shortcuts import render_to_response
from gibbs import reaction
from gibbs import reaction_form
from gibbs import conditions

_REACTION_TEMPLATES_BY_SUBMIT = {'': 'reaction_page.html',
                                 'Update': 'reaction_page.html',
                                 'Save': 'print_reaction.html',
                                 'Reverse': 'reaction_page.html'}


def ReactionPage(request):    
    """Renders a page for a particular reaction."""
    form = reaction_form.ReactionForm(request.GET)
    if not form.is_valid():
        logging.error(form.errors)
        return HttpResponseBadRequest('Invalid reaction form.')
    
    # Figure out which template to render (based on which submit button was
    # pressed).
    rxn = reaction.Reaction.FromForm(form)
    if form.cleaned_submit == 'Reverse':
        rxn.SwapSides()
        rxn.conditions = conditions.StandardConditions()
    query = rxn.GetQueryString()
    
    # Render the template.
    if form.cleaned_submit not in _REACTION_TEMPLATES_BY_SUBMIT:
        logging.error('Unknown submit term for reaction page: ' + form.cleaned_submit)
        raise Http404
    template_name = _REACTION_TEMPLATES_BY_SUBMIT[form.cleaned_submit]
    return render_to_response(template_name, rxn.GetTemplateData(query))