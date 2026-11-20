from rest_framework import serializers


class BugAnalysisSerializer(serializers.Serializer):
    title = serializers.CharField(
        max_length=255,
        required=True
    )

    description = serializers.CharField(
        required=True
    )