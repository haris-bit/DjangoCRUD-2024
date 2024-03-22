# schema.py
import graphene
from graphene_django.types import DjangoObjectType
from .models import AdvanceStats

class AdvanceStatsType(DjangoObjectType):
    class Meta:
        model = AdvanceStats

class Query(graphene.ObjectType):
    all_advance_stats = graphene.List(AdvanceStatsType)

    def resolve_all_advance_stats(self, info):
        return AdvanceStats.objects.all()

class Mutation(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        minutes_played = graphene.String()
        games_played = graphene.Int()
        three_point_attempt_rate = graphene.Float()
        total_rebound_percentage = graphene.String()
        win_shares = graphene.Float()
        win_shares_per_48_minutes = graphene.Float()
        box_plus_minus = graphene.Float()
        value_over_replacement_player = graphene.Float()

    advance_stats = graphene.Field(AdvanceStatsType)

    def mutate(self, info, **kwargs):
        advance_stats = AdvanceStats(**kwargs)
        advance_stats.save()
        return Mutation(advance_stats=advance_stats)
        

schema = graphene.Schema(query=Query, mutation=Mutation)
