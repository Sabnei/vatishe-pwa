"""URLs del módulo de seguridad y usuarios (RF-001)."""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from apps.cuentas import views
from apps.cuentas.forms import (
    CambiarContrasenaForm,
    EstablecerContrasenaForm,
    RecuperarContrasenaForm,
)

app_name = "cuentas"

urlpatterns = [
    # --- Autenticación ---
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="cuentas/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # --- Cambio de contraseña (usuario autenticado) ---
    path(
        "contrasena/cambiar/",
        auth_views.PasswordChangeView.as_view(
            template_name="cuentas/password_change.html",
            form_class=CambiarContrasenaForm,
            success_url=reverse_lazy("cuentas:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "contrasena/cambiar/listo/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="cuentas/password_change_done.html"
        ),
        name="password_change_done",
    ),

    # --- Recuperación de contraseña (por correo) ---
    path(
        "contrasena/recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="cuentas/password_reset.html",
            form_class=RecuperarContrasenaForm,
            email_template_name="cuentas/password_reset_email.txt",
            subject_template_name="cuentas/password_reset_subject.txt",
            success_url=reverse_lazy("cuentas:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "contrasena/recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="cuentas/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "contrasena/recuperar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="cuentas/password_reset_confirm.html",
            form_class=EstablecerContrasenaForm,
            success_url=reverse_lazy("cuentas:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "contrasena/recuperar/listo/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="cuentas/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    # --- Gestión de usuarios (Admin) e inquilinos ---
    path("usuarios/", views.GestionUsuariosView.as_view(), name="gestion_usuarios"),
    path("usuarios/nuevo/", views.NuevoInquilinoView.as_view(), name="nuevo_inquilino"),
    path(
        "usuarios/<int:pk>/",
        views.PerfilInquilinoAdminView.as_view(),
        name="perfil_inquilino_admin",
    ),
    path(
        "usuarios/<int:pk>/editar/",
        views.EditarInquilinoView.as_view(),
        name="editar_inquilino",
    ),
    path(
        "usuarios/<int:pk>/estado/",
        views.CambiarEstadoInquilinoView.as_view(),
        name="cambiar_estado_inquilino",
    ),

    # --- Perfil propio (Inquilino) ---
    path("mi-perfil/", views.MiPerfilView.as_view(), name="mi_perfil"),
]
