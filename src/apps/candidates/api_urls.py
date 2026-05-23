from django.urls import path

from . import api_views

urlpatterns = [
    path("search/countries", api_views.country_autocomplete, name="api_country_autocomplete"),
    path("search/first-names", api_views.first_name_autocomplete, name="api_first_name_autocomplete"),
    path("search/regions", api_views.region_autocomplete, name="api_region_autocomplete"),
    path("search/cities", api_views.city_autocomplete, name="api_city_autocomplete"),
    path("search/start", api_views.search_start, name="api_search_start"),
    path("search/step/<int:step>", api_views.search_step, name="api_search_step"),
    path("search/session/<str:token>/status", api_views.search_status, name="api_search_status"),
    path("search/session/<str:token>/profile", api_views.search_profile, name="api_search_profile"),
    path("candidates/create", api_views.candidate_create, name="api_candidate_create"),
    path("candidates/<int:candidate_id>/enrichment", api_views.candidate_enrichment, name="api_candidate_enrichment"),
    path("candidates/<int:candidate_id>/vote", api_views.candidate_vote, name="api_candidate_vote"),
    path("candidates/<int:candidate_id>/votes", api_views.candidate_votes, name="api_candidate_votes"),
]
