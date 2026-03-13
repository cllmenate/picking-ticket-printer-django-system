from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_scope = "auth"


class CustomTokenRefreshView(TokenRefreshView):
    throttle_scope = "auth"
