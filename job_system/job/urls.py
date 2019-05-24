from . import views
from django.urls import path
from .views import JobListView, JobUpdateView, JobCreateView, JobDeleteView

urlpatterns = [
    path('', JobListView.as_view(), name='job-list'),
    path('job/<int:pk>/update/', JobUpdateView.as_view(), name='job-update'),
    path('job/<int:pk>/delete/', JobDeleteView.as_view(), name='job-delete'),
    path('job/<int:pk>/run/', views.run_task, name='job-run'),
    path('create/', JobCreateView.as_view(), name='job-create'),

]