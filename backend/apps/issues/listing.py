"""
Issue list helpers - pagination, sorting and search (Week 2, Nandhini).

Kept in its own module so the Issue views stay small and merge cleanly:
the list view only has to point at these classes.

Query parameters supported on GET /api/v1/bugs/
------------------------------------------------
page, page_size    Pagination (default 10, max 100)
ordering           created_at, updated_at, id, title, severity, priority, status
                   Prefix with '-' for descending. severity/priority/status sort by
                   real importance / workflow order, not alphabetically:
                   ordering=severity   -> Critical first
                   ordering=-severity  -> Trivial first
search             Multi-field search over title, description, module, tags,
                   reporter, assignee and project name/key. A bare id ("42")
                   or a ticket key ("BF-42") jumps straight to that issue.
module             Exact (case-insensitive) module filter
created_after      ISO date, e.g. 2026-11-01
created_before     ISO date, inclusive
unassigned         true -> only issues with no assignee
is_duplicate       true / false
"""

import re

from django.db.models import Case, IntegerField, Value, When
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend, OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination

from .models import IssuePriority, IssueSeverity, IssueStatus

# Lower rank = more important / earlier in the workflow
SEVERITY_ORDER = [
    IssueSeverity.CRITICAL, IssueSeverity.HIGH, IssueSeverity.MEDIUM,
    IssueSeverity.LOW, IssueSeverity.TRIVIAL,
]
PRIORITY_ORDER = [
    IssuePriority.URGENT, IssuePriority.HIGH, IssuePriority.MEDIUM, IssuePriority.LOW,
]
STATUS_ORDER = [
    IssueStatus.OPEN, IssueStatus.TRIAGED, IssueStatus.IN_PROGRESS,
    IssueStatus.CODE_REVIEW, IssueStatus.QA_TESTING, IssueStatus.CLOSED,
    IssueStatus.REOPENED,
]

# public ordering name -> annotation name
RANKED_FIELDS = {
    'severity': ('severity_rank', SEVERITY_ORDER),
    'priority': ('priority_rank', PRIORITY_ORDER),
    'status': ('status_rank', STATUS_ORDER),
}


class IssuePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class IssueSearchFilter(SearchFilter):
    """SearchFilter plus direct lookup by issue id or ticket key (e.g. BF-42)."""

    ticket_pattern = re.compile(r'^(?:(?P<key>[A-Za-z][A-Za-z0-9]{1,9})-)?(?P<number>\d+)$')

    def filter_queryset(self, request, queryset, view):
        terms = self.get_search_terms(request)
        if len(terms) == 1:
            match = self.ticket_pattern.match(terms[0])
            if match:
                queryset = queryset.filter(id=int(match.group('number')))
                if match.group('key'):
                    queryset = queryset.filter(project__key__iexact=match.group('key'))
                return queryset
        return super().filter_queryset(request, queryset, view)


class IssueOrderingFilter(OrderingFilter):
    """OrderingFilter that sorts severity / priority / status by rank, not alphabetically."""

    def filter_queryset(self, request, queryset, view):
        annotations = {}
        for annotation, order in RANKED_FIELDS.values():
            field = annotation.replace('_rank', '')
            annotations[annotation] = Case(
                *[When(**{field: value}, then=Value(rank)) for rank, value in enumerate(order, start=1)],
                default=Value(len(order) + 1),
                output_field=IntegerField(),
            )
        return super().filter_queryset(request, queryset.annotate(**annotations), view)

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if not ordering:
            return ordering
        mapped = []
        for term in ordering:
            descending = term.startswith('-')
            name = term.lstrip('-')
            if name in RANKED_FIELDS:
                name = RANKED_FIELDS[name][0]
            mapped.append(f"-{name}" if descending else name)
        # Stable tie-break so pages never repeat or skip rows
        if 'id' not in [t.lstrip('-') for t in mapped]:
            mapped.append('-id')
        return mapped


class IssueExtraFilterBackend(BaseFilterBackend):
    """Extra list filters: module, created_after, created_before, unassigned, is_duplicate."""

    @staticmethod
    def _as_bool(value):
        return str(value).lower() in ('true', '1', 'yes')

    @staticmethod
    def _as_date(name, value):
        parsed = parse_date(value)
        if parsed is None:
            raise ValidationError({name: "Enter a valid date in YYYY-MM-DD format."})
        return parsed

    def filter_queryset(self, request, queryset, view):
        params = request.query_params

        module = params.get('module')
        if module:
            queryset = queryset.filter(module__iexact=module)

        created_after = params.get('created_after')
        if created_after:
            queryset = queryset.filter(created_at__date__gte=self._as_date('created_after', created_after))

        created_before = params.get('created_before')
        if created_before:
            queryset = queryset.filter(created_at__date__lte=self._as_date('created_before', created_before))

        if params.get('unassigned') is not None and self._as_bool(params.get('unassigned')):
            queryset = queryset.filter(assignee__isnull=True)

        if params.get('is_duplicate') is not None:
            queryset = queryset.filter(is_duplicate=self._as_bool(params.get('is_duplicate')))

        return queryset
