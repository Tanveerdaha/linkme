"""DRF serializers for reactions."""

from rest_framework import serializers

from apps.reactions.models import Reaction


class ReactionToggleSerializer(serializers.Serializer):
    reaction_type = serializers.ChoiceField(
        choices=[Reaction.ReactionType.HEART],
        default=Reaction.ReactionType.HEART,
        required=False,
    )


class ReactionResultSerializer(serializers.Serializer):
    reacted = serializers.BooleanField()
    reaction_type = serializers.CharField(required=False)
    count = serializers.IntegerField()


class ReactionSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    heart = serializers.IntegerField()
