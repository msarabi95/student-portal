# -*- coding: utf-8  -*-
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.db.models import Sum
from django.core.exceptions import PermissionDenied
from django.views.decorators import csrf

from post_office import mail
from accounts.models import get_gender
from core import decorators
from core.models import StudentClubYear
from activities.models import Activity, Evaluation
from activities.forms import EvaluationForm
from activities.utils import get_club_notification_to, get_club_notification_cc
from clubs.models import Club
from clubs.utils import has_coordination_to_activity, get_user_coordination_and_deputyships, can_review_any_niqati, is_coordinator_or_deputy_of_any_club
from niqati.models import Category, Code, Code_Order, Code_Collection, Review, COUPON, SHORT_LINK
from niqati.forms import OrderForm, RedeemCodeForm


current_year = StudentClubYear.objects.get_current()

@login_required
def index(request):
    if request.user.has_perms('niqati.view_general_report'): # Superuser
        return HttpResponseRedirect(reverse('niqati:general_report'))
    elif can_review_any_niqati(request.user):
        return HttpResponseRedirect(reverse('niqati:list_pending_orders'))
    elif is_coordinator_or_deputy_of_any_club(request.user):
        user_clubs = get_user_coordination_and_deputyships(request.user)
        user_club = user_clubs.first()
        context = {'user_club': user_club}
        return render(request, "niqati/intro_coordinators.html", context)
    else: # Student Views
        return HttpResponseRedirect(reverse('niqati:submit'))

@login_required
def redeem(request, code=""):
    """
    GET: show the code submission form.
    POST: submit a code.
    """
    
    if current_year.niqati_closure_date and timezone.now() > current_year.niqati_closure_date:
        return render(request, "niqati/submit_closed.html")
    if request.user.coordination.current_year().exists():
        user_club = request.user.coordination.current_year().first()
        context = {'user_club': user_club}
        return render(request, "niqati/submit_coordinators.html", context)
    if request.method == "POST":
        form = RedeemCodeForm(request.user, request.POST)
        eval_form = EvaluationForm(request.POST)
        if form.is_valid() and eval_form.is_valid():
            result = form.process()
            messages.add_message(request, *result)
            eval_form.save(form.code.event, request.user)
            return HttpResponseRedirect(reverse("codes:submit"))
    elif request.method == "GET":
        form = RedeemCodeForm(request.user, initial={'string': code})
        eval_form = EvaluationForm()
    return render(request, "niqati/submit.html", {"form": form,  "eval_form": eval_form})
    
@login_required
def student_report(request):
    if request.user.coordination.current_year().exists():
        user_club = request.user.coordination.current_year().first()
        context = {'user_club': user_club}
        return render(request, "niqati/submit_coordinators.html", context)
    else:
        # calculate total points
        total_points = request.user.code_set.aggregate(total_points=Sum('points'))['total_points']
        if total_points is None:
            total_points = 0
        context = {'total_points': total_points}
        # TODO: sort codes
        return render(request, 'niqati/student_report.html', context)

# Club Views
@login_required
def coordinator_view(request, activity_id):
    """
    If request is GET, view orders.
    If POST, create codes.
    """

    activity = get_object_or_404(Activity, pk=activity_id)

    # --- Permission checks ---
    # Only the club coordinator has the permission to view
    # niqati orders
    if not has_coordination_to_activity(request.user, activity) \
       and not request.user.is_superuser:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = OrderForm(request.POST, activity=activity, user=request.user)
        if form.is_valid():
            order = form.save()
            reviewing_parent = activity.primary_club.get_next_niqati_reviewing_parent()
            # Make sure that a coordinator was assigned to the
            # reviewing club before trying to send an email
            # notification.
            if reviewing_parent and reviewing_parent.coordinator:
                list_pending_orders_url = reverse('niqati:list_pending_orders')
                full_url = request.build_absolute_uri(list_pending_orders_url)
                email_context = {'order': order, 'full_url': full_url}
                mail.send([reviewing_parent.coordinator.email],
                          template="niqati_order_submitted",
                          context=email_context)

                msg = u"تم إرسال الطلب؛ و سيتم إنشاء النقاط فور الموافقة عليه"
                messages.add_message(request, messages.SUCCESS, msg)
        else:
            msg = u"الرجاء ملء النموذج بشكل صحيح."
            messages.add_message(request, messages.ERROR, msg)
        return HttpResponseRedirect(reverse("activities:niqati_orders", args=(activity.id, )))
    elif request.method == 'GET':
        form = OrderForm(activity=activity, user=request.user)
        return render(request, 'niqati/activity_orders.html', {'activity': activity,
                                                           'form': form,
                                                           'active_tab': 'niqati'})

@login_required
def download_collection(request, pk, download_type):
    collection = get_object_or_404(Code_Collection, pk=pk)
    activity = collection.parent_order.episode.activity
    domain = Site.objects.get_current().domain
    domain =  'enjazportal.com' # REMOVE

    if not has_coordination_to_activity(request.user, activity) and \
       not request.user.is_superuser:
        raise PermissionDenied

    if download_type == COUPON:
        endpoint = "http://api.qrserver.com/v1/create-qr-code/?size=180x180&data=" + domain

        response = render(request, 'niqati/includes/coupons.html', {"collection": collection,
                                                                   "domain": domain,
                                                                   "endpoint": endpoint})
    elif download_type == SHORT_LINK:
        endpoint = "https://api-ssl.bitly.com/v3/shorten?format=txt&access_token=%(api_key)s&longUrl=" % {"api_key": settings.BITLY_KEY}

        response = render(request, 'niqati/includes/links.html', {"collection": collection,
                                                                 "domain": domain,
                                                                 "endpoint": endpoint})
    # Mark codes as downloaded
    collection.date_downloaded = timezone.now()

    return response

# Management Views

@login_required
@csrf.csrf_exempt
@decorators.ajax_only
@decorators.post_only
def review_order(request):
    order_pk = request.POST.get('pk')
    action = request.POST.get('action')
    order = get_object_or_404(Code_Order, pk=order_pk)
    niqati_reviewers = Club.objects.niqati_reviewing_parents(order)
    user_clubs = niqati_reviewers.filter(coordinator=request.user) | \
                 niqati_reviewers.filter(deputies=request.user)
    email_context = {'order': order}

    # Permission check
    if request.user.has_perm('activities.change_code'):
        reviewer_club = None
    elif user_clubs.exists():
        reviewer_club = user_clubs.first()
    else: # If not a superuser, nor has reviewer 
        raise PermissionDenied

    if action == 'accept':
        is_approved = True

        # If the reviewer belongs to a reviewer club (i.e. not the
        # superuser), then check if we have a niqati reviewing parent.
        # If so, assign the order to them.  If not, consider the order
        # approved and email the submitter.  Otherwise, if the review
        # does not belong to a reviewer club (i.e. superuser),
        # consider the order approved.
        if reviewer_club:
            next_parent = reviewer_club.get_next_niqati_reviewing_parent()
            if next_parent:
                order.assignee = next_parent
                order.is_approved = None
                if next_parent.coordinator:
                    list_pending_orders_url = reverse('niqati:list_pending_orders')
                    full_url = request.build_absolute_uri(list_pending_orders_url)
                    email_context['full_url'] = full_url
                    email_context['last_reviewer'] = reviewer_club
                    email_context['upcoming_reviewer'] = next_parent
                    mail.send(next_parent.coordinator.email,
                              template="niqati_approved_to_next_reviwer",
                              context=email_context)
            else:
                order.assignee = None
                order.is_approved = True
        else: # superuser
            order.assignee = None
            order.is_approved = True

        if order.is_approved:
            order.create_codes()
            niqati_orders_url = reverse('activities:niqati_orders', args=(order.episode.activity.pk,))
            full_url = request.build_absolute_uri(niqati_orders_url)
            email_context['full_url'] = full_url            
            mail.send(get_club_notification_to(order.episode.activity),
                      cc=get_club_notification_cc(order.episode.activity),
                      template="niqati_approved_to_submitter",
                      context=email_context)

    elif action == 'reject':
        is_approved = False
        order.assignee = None
        order.is_approved = False
        niqati_orders_url = reverse('activities:niqati_orders', args=(order.episode.activity.pk,))
        full_url = request.build_absolute_uri(niqati_orders_url)
        email_context['full_url'] = full_url

        mail.send(get_club_notification_to(order.episode.activity),
                  cc=get_club_notification_cc(order.episode.activity),
                  template="niqati_rejected_to_submitter",
                  context=email_context)
    else:
        raise Exception(u'تصرف خاطئ.')

    Review.objects.create(order=order,
                          reviewer=request.user,
                          reviewer_club=reviewer_club,
                          is_approved=is_approved)
    order.save()

@login_required
def list_pending_orders(request):
    user_clubs = get_user_coordination_and_deputyships(request.user)
    user_niqati_reviewing_clubs = user_clubs.filter(can_review_niqati=True)
    if not request.user.has_perm('activities.change_code') and \
       not user_niqati_reviewing_clubs.exists():
        raise PermissionDenied
    activities_with_pending_orders = Activity.objects.filter(episode__code_order__assignee__in=user_niqati_reviewing_clubs,
                                                             episode__code_order__is_approved__isnull=True).distinct()
    context = {'activities_with_pending_orders': activities_with_pending_orders}
    return render(request, 'niqati/approve.html', context)

@login_required
@permission_required('niqati.view_general_report', raise_exception=True)
def general_report(request):
    users = User.objects.annotate(point_sum=Sum('code__category__points')).filter(point_sum__gt=0).order_by('-point_sum')
    return render(request, 'niqati/general_report.html', {'users': users})
