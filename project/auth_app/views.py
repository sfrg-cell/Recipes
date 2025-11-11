from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import logging

from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger('api')


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info('POST request to RegisterView')
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                logger.info(f'User registered successfully: {user.username}')
                return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
            
            logger.warning(f'User registration validation failed: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f'Error in RegisterView: {str(e)}', exc_info=True)
            return Response(
                {"error": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info('POST request to LoginView')
        try:   
            username = request.data.get('username')
            password = request.data.get('password')
            logger.debug(f'Login attempt for user: {username}')
            user = authenticate(username=username, password=password)

            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            
            logger.warning(f'Failed login attempt for user: {username}')
            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            logger.error(f'Error in LoginView: {str(e)}', exc_info=True)
            return Response(
                {"error": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info(f'GET request to UserView for user: {request.user.username}')
        try:
            serializer = UserSerializer(request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f'Error in UserView: {str(e)}', exc_info=True)
            return Response(
                {"error": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )