from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .serializers import BugAnalysisSerializer
from .services import analyze_bug


class AnalyzeDraftView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = BugAnalysisSerializer(data=request.data)

        if serializer.is_valid():

            title = serializer.validated_data["title"]
            description = serializer.validated_data["description"]

            prediction = analyze_bug(title, description)

            return Response({
                "success": True,
                "message": "Bug analysis completed",
                "data": prediction
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)