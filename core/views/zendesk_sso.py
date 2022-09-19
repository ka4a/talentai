import jwt
from uuid import uuid4
from datetime import datetime
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from core.serializers import ZendeskJWTSerializer


class ZendeskJWTView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_id='zendesk_sso_jwt_token_retrieve',
        responses={200: ZendeskJWTSerializer},
    )
    def get(self, request):
        user = self.request.user
        payload = {
            'email': user.email,
            'name': user.full_name,
            'external_id': str(user.id),
            'iat': int(datetime.utcnow().timestamp()),
            'jti': uuid4().hex,
        }
        token = jwt.encode(
            payload=payload,
            key=settings.ZENDESK_SSO_SECRET,
            algorithm=settings.ZENDESK_SSO_JWT_ENCODING,
        )

        return Response({'token': token}, HTTP_200_OK)
