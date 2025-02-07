import logging
from typing import Dict

from .journal import Journal
from .get_downloadable_analyses import get_downloadable_analyses
from .download_analysis import download_analysis
from sgqlc.endpoint.http import HTTPEndpoint
from .parse_args import parse_args

log = logging.getLogger(__name__)


def get_unfinished_analyses() -> Dict[str, str]:
    """Yields analyses that are available for download.
    Polls for more analyses and yields them until no more are available.
    """
    journal = Journal.singleton()
    requested_federal_states = parse_args().federal_states
    unfinished = {pk:state for pk, state in journal.analysis_states.items()
            if pk not in journal.synced_analyses and (requested_federal_states is None or state in requested_federal_states)}
    return unfinished


def download_completed_analyses(client: HTTPEndpoint) -> bool:
    """Downloads the analyses that have been completed."""
    journal = Journal.singleton()
    args = parse_args()
    for analysis in get_downloadable_analyses(client):
        if not analysis.pk in journal.synced_analyses:
            if analysis.pk in journal.analysis_states:
                log.info(f"Downloading analysis {analysis.pk} for state {journal.analysis_states[analysis.pk]}")
                download_analysis(analysis)
                log.info(f"Downloaded analysis {analysis.pk}")
            elif args.verbose:
                # Skip analyses that are not in the journal (e.g. manually started by user)
                log.info(f"Analysis {analysis.pk} missing metadata; skipping download")
        elif args.verbose:
            log.info(f"Analysis {analysis.pk} already downloaded")
    unfinished_analyses = get_unfinished_analyses()
    for pk, state in unfinished_analyses.items():
        log.info(f"Analysis {pk} for state {state} not yet finished")
    return len(unfinished_analyses) == 0
