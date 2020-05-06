from django.urls import path

from . import views

urlpatterns = [
    # ex: /champselect/
    path('', views.CreateDropDownView.as_view(), name='index'),
    # ex: /champselect/5/
    path('<int:question_id>/',views.detail, name='detail'),
    # ex: /champselect/5/results/
    path('<int:question_id>/results/', views.results, name='results'),
    # ex: /champselect/5/vote/
    path('<int:question_id>/vote/', views.vote, name='vote'),
    # ex: /champselect/success/
    path('success/', views.calculate, name='calculate'),
]