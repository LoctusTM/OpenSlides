#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    openslides.agenda.views
    ~~~~~~~~~~~~~~~~~~~~~~~

    Views for the agenda app.

    :copyright: 2011 by the OpenSlides team, see AUTHORS.
    :license: GNU GPL, see LICENSE for more details.
"""
from reportlab.platypus import Paragraph

from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.core.context_processors import csrf
from django.views.generic.detail import SingleObjectMixin

from utils.pdf import stylesheet
from utils.views import (TemplateView, RedirectView, UpdateView, CreateView,
                         DeleteView, PDFView, FormView, DetailView)
from utils.template import Tab

from config.models import config

from projector.api import get_active_slide, set_active_slide

from agenda.models import Item
from agenda.api import is_summary
from agenda.forms import ItemOrderForm, ItemForm, ConfigForm


class Overview(TemplateView):
    permission_required = 'agenda.can_see_agenda'
    template_name = 'agenda/overview.html'

    def get_context_data(self, **kwargs):
        context = super(Overview, self).get_context_data(**kwargs)
        context.update({
            'items': Item.objects.all(),
            'overview': get_active_slide(only_sid=True) == 'agenda_show',
            'summary': is_summary(),
        })
        return context

    def post(self, request, *args, **kwargs):
        #todo: check for permission
        context = self.get_context_data(**kwargs)
        #todo: check for any erros in the forms befor saving the data
        for item in Item.objects.all():
            form = ItemOrderForm(request.POST, prefix="i%d" % item.id)
            if form.is_valid():
                try:
                    item.parent = Item.objects.get(
                                       id=form.cleaned_data['parent'])
                except Item.DoesNotExist:
                    item.parent = None
                item.weight = form.cleaned_data['weight']
                item.save()
        return self.render_to_response(context)


class View(DetailView):
    permission_required = 'agenda.can_see_agenda'
    template_name = 'agenda/view.html'
    model = Item
    context_object_name = 'item'


class SetActive(RedirectView, SingleObjectMixin):
    """
    Set an Item as the active one.
    """
    url = 'item_overview'
    allow_ajax = True
    permission_required = 'agenda.can_manage_agenda'
    model = Item

    def get_ajax_context(self, **kwargs):
        context = super(SetActive, self).get_ajax_context(**kwargs)
        context.update({
            'active': kwargs['pk'],
            'summary': is_summary(),
        })
        return context

    def pre_redirect(self, request, *args, **kwargs):
        summary = kwargs['summary']
        if kwargs['pk'] == "0":
            set_active_slide("agenda_show")
        else:
            self.object = self.get_object()
            self.object.set_active(summary)
        config["bigger"] = 100
        config["up"] = 0
        return super(SetActive, self).pre_redirect(request, *args, **kwargs)


class SetClosed(RedirectView, SingleObjectMixin):
    """
    Close or open an Item.
    """
    permission_required = 'agenda.can_manage_agenda'
    allow_ajax = True
    url = 'item_overview'
    model = Item

    def get_ajax_context(self, **kwargs):
        context = super(SetClosed, self).get_ajax_context(**kwargs)
        closed = kwargs['closed']
        if closed:
            link = reverse('item_open', args=[self.object.id])
        else:
            link = reverse('item_close', args=[self.object.id])
        context.update({
            'closed': kwargs['closed'],
            'link': link,
        })
        return context

    def pre_redirect(self, request, *args, **kwargs):
        self.object = self.get_object()
        closed = kwargs['closed']
        self.object.set_closed(closed)
        return super(SetClosed, self).pre_redirect(request, *args, **kwargs)


class ItemUpdate(UpdateView):
    permission_required = 'agenda.can_manage_agenda'
    template_name = 'agenda/edit.html'
    model = Item
    context_object_name = 'item'
    form_class = ItemForm
    success_url = 'item_overview'


class ItemCreate(CreateView):
    permission_required = 'agenda.can_manage_agenda'
    template_name = 'agenda/edit.html'
    model = Item
    context_object_name = 'item'
    form_class = ItemForm
    success_url = 'item_overview'


class ItemDelete(DeleteView):
    """
    Delete an Item.
    """
    permission_required = 'agenda.can_manage_agenda'
    model = Item
    url = 'item_overview'

    def pre_post_redirect(self, request, *args, **kwargs):
        self.object = self.get_object()

        if 'all' in request.POST:
            self.object.delete()
            messages.success(request, _("Item <b>%s</b> and his children were successfully deleted.") % self.object)
        else:
            for child in self.object.get_children():
                child.parent = self.object.parent
                child.save()
            self.object.delete()
            messages.success(request, _("Item <b>%s</b> was successfully deleted.") % self.object)

    def gen_confirm_form(self, request, message, url, singleitem=None):
        if singleitem:
            messages.warning(request, '%s<form action="%s" method="post"><input type="hidden" value="%s" name="csrfmiddlewaretoken"><input type="submit" value="%s" /> <input type="button" value="%s"></form>' % (message, url, csrf(request)['csrf_token'], _("Yes"), _("No")))
        else:
            messages.warning(request, '%s<form action="%s" method="post"><input type="hidden" value="%s" name="csrfmiddlewaretoken"><input type="submit" value="%s" /> <input type="submit" name="all" value="%s" /> <input type="button" value="%s"></form>' % (message, url, csrf(request)['csrf_token'], _("Yes"), _("Yes, with all child items."), _("No")))

    def confirm_form(self, request, object, name=None):
        if name is None:
            name = object
        if object.children:
            self.gen_confirm_form(request, _('Do you really want to delete <b>%s</b>?') % name, object.get_absolute_url('delete'), False)
        else:
            self.gen_confirm_form(request, _('Do you really want to delete <b>%s</b>?') % name, object.get_absolute_url('delete'), True)


class AgendaPDF(PDFView):
    permission_required = 'agenda.can_see_agenda'
    filename = _('Agenda')
    document_title = _('Agenda')

    def append_to_pdf(self, story):
        for item in Item.objects.all():
            ancestors = item.get_ancestors()
            if ancestors:
                space = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" * ancestors.count()
                story.append(Paragraph("%s%s" % (space, item.title), stylesheet['Subitem']))
            else:
                story.append(Paragraph(item.title, stylesheet['Item']))


class Config(FormView):
    permission_required = 'config.can_manage_config'
    form_class = ConfigForm
    template_name = 'agenda/config.html'

    def get_initial(self):
        return {'agenda_countdown_time': config['agenda_countdown_time']}

    def form_valid(self, form):
        config['agenda_countdown_time'] = form.cleaned_data['agenda_countdown_time']
        messages.success(self.request, _('Agenda settings successfully saved.'))
        return super(Config, self).form_valid(form)


def register_tab(request):
    selected = True if request.path.startswith('/agenda/') else False
    return Tab(
        title=_('Agenda'),
        url=reverse('item_overview'),
        permission=request.user.has_perm('agenda.can_see_agenda') or request.user.has_perm('agenda.can_manage_agenda'),
        selected=selected,
    )
