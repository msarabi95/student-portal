0# -*- coding: utf-8  -*-
from django import forms
from django.forms.widgets import TextInput

from accounts.utils import get_user_gender
from events.models import NonUser, Session, Registration, Abstract, \
                          AbstractFigure, Initiative, InitiativeFigure, \
                          Criterion, CriterionValue, Evaluation,CaseReport, \
                          AbstractPoster, Attendance, Question, SurveyQuestion, \
                          SurveyResponse, SurveyAnswer
from django.forms.models import inlineformset_factory

class NonUserForm(forms.ModelForm):
    class Meta:
        model = NonUser
        fields = ['ar_first_name', 'ar_middle_name', 'ar_last_name',
                  'en_first_name', 'en_middle_name', 'en_last_name',
                  'email', 'mobile_number', 'university', 'college',
                  'gender']
        
class RegistrationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.event = kwargs.pop("event")
        super(RegistrationForm, self).__init__(*args, **kwargs)
        time_slots = Session.objects.filter(event=self.event, time_slot__isnull=False).values_list('time_slot', flat=True).distinct()
        for time_slot in time_slots:
            time_slot_sessions = Session.objects.filter(event=self.event, time_slot=time_slot)
            if self.user:
                user_gender = get_user_gender(self.user)
                time_slot_sessions = Session.objects.filter(event=self.event,
                                                            time_slot=time_slot,
                                                            gender__in=['', user_gender])
            # Add as many time slot fields as many priorities we have.
            for priority in range(1, self.event.priorities + 1):
                self.fields['time_slot_%s_%s' % (time_slot, priority)] = forms.ModelChoiceField(time_slot_sessions, required=False)
                self.fields['time_slot_%s_%s' % (time_slot, priority)].widget.attrs['class'] = 'form-control'

        untimed_sessions = Session.objects.filter(event=self.event, time_slot__isnull=True)

        for untimed_session in untimed_sessions:
            self.fields['session_%s' % untimed_session.code_name] = forms.BooleanField(label=untimed_session.name,
                                                                                       required=False)

    def save(self, nonuser=None):
        timed_session_fields = [field_name for field_name in self.cleaned_data
                                if field_name.startswith('time_slot_') and self.cleaned_data[field_name]]
        untimed_session_code_names = [field_name.split('_')[-1] for field_name in self.cleaned_data
                               if field_name.startswith('session_') and self.cleaned_data[field_name]]

        # If no sessions were selected, do not register.
        if not untimed_session_code_names and \
           not timed_session_fields:
            return

        if self.user:
            registration = Registration.objects.create(user=self.user)
        elif nonuser:
            registration = Registration.objects.create(nonuser=nonuser)

        for timed_session_field in timed_session_fields:
            session = self.cleaned_data[timed_session_field]
            if session:
                if timed_session_field.endswith("_1"):
                    registration.first_priority_sessions.add(session)
                elif timed_session_field.endswith("_2"):
                    registration.second_priority_sessions.add(session)

        for session_code_name in untimed_session_code_names:
            session = Session.objects.get(event=self.event, code_name=session_code_name)
            registration.first_priority_sessions.add(session)

        return registration

class AbstractForm(forms.ModelForm):
    class Meta:
        model = Abstract
        fields = ['title', 'authors', 'university', 'college',
                  'study_field', 'presenting_author', 'email',
                  'phone', 'level', 'presentation_preference',
                  'introduction','methodology', 'results',
                  'discussion', 'conclusion', 'was_published',
                  'was_presented_at_others',
                  'was_presented_previously',]

AbstractFigureFormset = inlineformset_factory(Abstract,
                                              AbstractFigure,
                                              fields=['figure'],
                                              max_num=1,
                                              validate_max=True)


class AbstractFigureForm(forms.ModelForm):
    class Meta:
        model = AbstractFigure
        fields = ['figure']

class AbstractPosterForm(forms.ModelForm):
    class Meta:
        model = AbstractPoster
        fields = ['first_image','second_image','poster_powerpoint']


class AbstractPresentationForm(AbstractPosterForm):
    class Meta:
        model= AbstractPoster
        fields =['presentation_file']

class CaseReportForm(forms.ModelForm):
    class Meta:
        model = CaseReport
        fields = ['title', 'authors', 'university', 'college', 'email','phone',
                  'introduction','patient_info', 'clinical_presentation',
                  'diagnosis', 'treatment', 'outcome','discussion','conclusion',
                  'was_published',
                  'was_presented_at_others',
                  'was_presented_previously','study_field']

class EvaluationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.evaluator = kwargs.pop("evaluator")
        super(EvaluationForm, self).__init__(*args, **kwargs)

        default_choices = [(i, i) for i in range(11)]
        for criterion in Criterion.objects.filter(events=self.instance.abstract.event):
            field_name = 'criterion_' + str(criterion.code_name)
            initial_value = None
            if self.instance.id:
                try:
                    criterion_value = CriterionValue.objects.get(evaluation=self.instance,
                                                                 criterion=criterion)
                    initial_value = criterion_value.value
                except CriterionValue.DoesNotExist:
                    pass

            self.fields[field_name] = forms.IntegerField(label=criterion.human_name, initial=initial_value,
                                                         widget=forms.RadioSelect(choices=default_choices, ),
                                                         required=True,
                                                         help_text=criterion.instructions)

    def save(self):
        # Create only if the instance has not been saved (i.e. we are
        # not editing)
        if not self.instance.id:
            evaluation = Evaluation.objects.create(abstract=self.instance.abstract,
                                                   evaluator=self.evaluator)
        else:
            evaluation = self.instance
            evaluation.evaluator = self.evaluator
            evaluation.save()

        for field_name in self.cleaned_data:
            value = self.cleaned_data[field_name]
            criterion_name = field_name.replace('criterion_', '')
            criterion = Criterion.objects.get(code_name=criterion_name)

            try:
                if self.instance.id:
                    criterion_value = CriterionValue.objects.get(criterion=criterion,
                                                                 evaluation=evaluation)
                else:
                    raise CriterionValue.DoesNotExist
            except CriterionValue.DoesNotExist:
                CriterionValue.objects.create(criterion=criterion,
                                              evaluation=evaluation,
                                              value=value)
            else:
                criterion_value.value = value
                criterion_value.save()

        return evaluation

    class Meta:
        model = Evaluation
        exclude = ['evaluator', 'abstract']

class InitiativeForm(forms.ModelForm):
    class Meta:
        model = Initiative
        fields = ['name', 'definition', 'goals',
                  'target','achievements', 'future_goals',
                  'goals_from_participating', 'members',
                  'sponsors', 'email', 'social']

InitiativeFigureFormset = inlineformset_factory(Initiative,
                                              InitiativeFigure,
                                              fields=['figure'])

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['category']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

class SurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.session = kwargs.pop("session")
        self.optional_questions = self.mandatory_questions = SurveyQuestion.objects.none()
        if self.session.mandatory_survey:
            self.mandatory_questions = self.session.mandatory_survey.survey_questions.all()
        if self.session.optional_survey:
            self.optional_questions = self.session.optional_survey.survey_questions.all()
        super(SurveyForm, self).__init__(*args, **kwargs)
        for question in (self.mandatory_questions | self.optional_questions):
            field_name = 'question_' + str(question.pk)
            if question.category == "O":
                self.fields[field_name] = forms.CharField(label=question.text,
                                                          widget=forms.Textarea)
            elif question.category == "S":
                from django.utils.html import format_html
                choices = [(i, i) for i in range(11)]
                if question.is_english:
                    # This is used in the template to add
                    # 'english-field' to the label tag by JavaScript.
                    label = format_html(u"<span class='english'>{}</span>", question.text)
                else:
                    label = question.text
                self.fields[field_name] = forms.IntegerField(label=label,
                                                             widget=forms.RadioSelect(choices=choices))
            if question in self.optional_questions:
                self.fields[field_name].required = False

    def save(self, user):
        field_names = [field_name for field_name in self.cleaned_data
                       if field_name.startswith("question_")]
        mandatory_response = None
        optional_response = None 

        for field_name in field_names:
            question_pk = field_name.lstrip("question_")
            question = SurveyQuestion.objects.get(pk=question_pk)
            if question in self.optional_questions:
                survey = self.session.optional_survey
                if not optional_response:
                    optional_response = SurveyResponse.objects\
                                                      .create(survey=survey,
                                                              session=self.session,
                                                              user=user)
                response = optional_response
            if question in self.mandatory_questions:
                survey = self.session.mandatory_survey
                if not mandatory_response:
                    mandatory_response = SurveyResponse.objects\
                                                       .create(survey=survey,
                                                               session=self.session,
                                                               user=user)
                response = mandatory_response
            arguments = {'question': question,
                         'survey_response': response}
            if question.category == 'O':
                arguments['text_value'] = self.cleaned_data[field_name]
            elif question.category == 'S':
                arguments['numerical_value'] = self.cleaned_data[field_name]
            SurveyAnswer.objects.create(**arguments)
