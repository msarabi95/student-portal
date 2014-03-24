# -*- coding: utf-8  -*-
from django.db import models
from django.contrib.auth.models import User

class Activity(models.Model):
    # For now, we will follow the current practice: only one club will
    # be considered the primary orginzier.  Others will be cosidered
    # secondary.
    #clubs = models.ManyToManyField('clubs.Club',
    #                               verbose_name=u"النوادي")
    primary_club = models.ForeignKey('clubs.Club', null=True,
                                     on_delete=models.SET_NULL,
                                     related_name='primary_activity',
                                     verbose_name=u"النادي المنظم")
    secondary_clubs = models.ManyToManyField('clubs.Club', blank=True,
                                            null=True,
                                            related_name="secondary_activity",
                                            verbose_name=u"النوادي المساندة")
    name = models.CharField(max_length=200, verbose_name=u"الاسم")
    description = models.TextField(verbose_name=u"الوصف")
    requirements = models.TextField(blank=True,
                                    verbose_name=u"المتطلبات")
    submitter = models.ForeignKey(User, null=True,
                                  on_delete=models.SET_NULL)
    submission_date = models.DateTimeField('date submitted',
                                           auto_now_add=True)
    date = models.DateTimeField('date')
    edit_date = models.DateTimeField('date edited', auto_now=True)
    approval_date = models.DateTimeField(null=True,
                                         verbose_name=u"تاريخ الاعتماد")
    # For is_approved, we have three chocies:
    #   None: Not reviewed yet.
    #   True: Accepted.
    #   False: Rejected.
    is_approved = models.NullBooleanField(default=None)
    is_editable = models.BooleanField(default=True)
    collect_participants = models.BooleanField(default=False,
                                               verbose_name=u"اسمح بالتسجيل؟")
    inside_collaborators = models.TextField(blank=True,
                                            verbose_name=u"المتعاونون من داخل الجامعة")
    outside_collaborators = models.TextField(blank=True,
                                             verbose_name=u"المتعاونون من خارج الجامعة")
    participants = models.IntegerField(verbose_name=u"عدد المشاركين")
    organizers = models.IntegerField(verbose_name=u"عدد المنظمين")

    class Meta:
        permissions = (
            ("view_activity", "Can view all available activities."),
        )


    def __unicode__(self):
        return str(self.id)

class Review(models.Model):
    activity = models.OneToOneField(Activity, verbose_name=u" النشاط")
    reviewer = models.ForeignKey(User, null=True,
                                 on_delete=models.SET_NULL)
    review_date = models.DateTimeField('date reviewed', auto_now_add=True)
    clubs_notes = models.TextField(blank=True,
                                   verbose_name=u"ملاحظات على الأندية")
    name_notes = models.TextField(blank=True,
                                  verbose_name=u"ملاحظات على الاسم")
    description_notes = models.TextField(blank=True,
                                        verbose_name=u"ملاحظات على الوصف")
    requirement_notes = models.TextField(blank=True,
                                        verbose_name=u"ملاحظات على المتطلبات")
    inside_notes = models.TextField(blank=True,
                                            verbose_name=u"ملاحظات المتعاونون من داخل الجامعة")
    outside_notes = models.TextField(blank=True,
                                             verbose_name=u"ملاحظات المتعاونون من خارج الجامعة")
    participants_notes = models.TextField(blank=True,
                                          verbose_name=u"ملاحظات على عدد المشاركين")
    organizers_notes = models.TextField(blank=True,
                                        verbose_name=u"ملاحظات على عدد المنظمين")
    class Meta:
        permissions = (
            ("view_review", "Can view all available activities."),
        )

    def __unicode__(self):
        return str(self.id)


class Participation(models.Model):
    activity = models.OneToOneField(Activity, verbose_name=u" طاشنلا")
    user = models.ForeignKey(User, null=True,
                             on_delete=models.SET_NULL)
    submission_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = (
            ("view_participation", "Can view all available participations."),
        )
