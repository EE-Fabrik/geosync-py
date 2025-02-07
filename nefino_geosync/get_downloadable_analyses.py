import logging
from time import sleep
from typing import Generator, Protocol

from .journal import Journal
from .api_client import get_analyses_operation
from .schema import DateTime, Status
from .graphql_errors import check_errors
from sgqlc.endpoint.http import HTTPEndpoint
from .parse_args import parse_args


log = logging.getLogger(__name__)


# Let's give a quick description of what we want to be fetching.
# This does depend on what get_analysis_operation() actually does.
class AnalysisResult(Protocol):
    status: Status
    pk: str
    url: str
    started_at: DateTime


def is_relevant_federal_state(analysis, journal, requested_federal_states):
    if requested_federal_states:
        federal_state = journal.analysis_states.get(analysis.pk, "unknown")
        return federal_state in requested_federal_states
    else:
        return True

def get_downloadable_analyses(client: HTTPEndpoint) -> Generator[AnalysisResult, None, None]:
    """Yields analyses that are available for download.
    Polls for more analyses and yields them until no more are available.
    """
    args = parse_args()
    verbose = args.verbose
    skip_unfinished = args.skip_unfinished
    requested_federal_states = args.federal_states
    op = get_analyses_operation()
    reported_pks = set()
    journal = Journal.singleton()
    log.info("Checking for analyses to download...")
    while True:
        data = client(op)
        check_errors(data)
        analyses = op + data
        found_outstanding_analysis = False
        for analysis in analyses.analysis_metadata:
            if is_relevant_federal_state(analysis, journal, requested_federal_states):
                if analysis.status == Status("PENDING") or analysis.status == Status("RUNNING"):
                    if verbose:
                        log.info(f"Analysis {analysis.pk} is still pending or running.")
                    found_outstanding_analysis = True
                if analysis.status == Status("SUCCESS") and analysis.pk not in reported_pks:
                    reported_pks.add(analysis.pk)
                    yield analysis
            elif verbose:
                log.info(f"Skipping analysis {analysis.pk} because it is not in the list of requested federal states")

        if skip_unfinished or not found_outstanding_analysis:
            break
        if verbose:
            log.info("Waiting for more analyses to finish...")
        sleep(10)
