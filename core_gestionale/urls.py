from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views # <-- Importa le viste di login/logout di Django
from gestione_rifiuti import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.homepage, name='homepage'),
    path('punto-cassa/', views.punto_cassa, name='punto_cassa'),
    path('profilo/', views.profilo_cittadino, name='profilo_cittadino'),
    path('area-riscatto/', views.area_riscatto, name='area_riscatto'),
    path('login/', auth_views.LoginView.as_view(template_name='gestione_rifiuti/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='gestione_rifiuti/logout.html'), name='logout'),
    path('registrazione/', views.registrazione_cittadino, name='registrazione'),
    path('password-reset/',auth_views.PasswordResetView.as_view(template_name='gestione_rifiuti/password_reset.html'), name='password_reset'),
    path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(template_name='gestione_rifiuti/password_reset_done.html'),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='gestione_rifiuti/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/',auth_views.PasswordResetCompleteView.as_view(template_name='gestione_rifiuti/password_reset_complete.html'), name='password_reset_complete'),
    path('dashboard-admin/', views.dashboard_admin, name='dashboard_admin'),
    path('gestisci-rifiuto/', views.gestisci_rifiuto, name='aggiungi_rifiuto'),
    path('gestisci-rifiuto/<int:pk>/', views.gestisci_rifiuto, name='modifica_rifiuto'),
    path('modifica-conferimento/<int:pk>/', views.modifica_conferimento_admin, name='modifica_conferimento'),
]