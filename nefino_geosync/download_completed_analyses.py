import datetime
import logging
from typing import Dict, Optional

from .journal import Journal
from .get_downloadable_analyses import get_downloadable_analyses
from .download_analysis import download_analysis
from sgqlc.endpoint.http import HTTPEndpoint
from .parse_args import parse_args

log = logging.getLogger(__name__)


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
    unfinished_analyses = journal.get_non_downloaded_analyses(client, args.federal_states)
    for pk, state in unfinished_analyses.items():
        log.info(f"Analysis {pk} for state {state} not yet finished")
    return len(unfinished_analyses) == 0


def get_failed_analyses(client: HTTPEndpoint, failed_since: Optional[datetime] = None) -> Dict[str, str]:
    """Checks for failed analyses and returns a dictionary of failed analyses."""
    journal = Journal.singleton()
    args = parse_args()
    if not failed_since:
        failed_since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    failed_analyses = journal.get_failed_analyses(client, args.federal_states, failed_since)
    if failed_analyses:
        log.warning(f"{len(failed_analyses)} analyses failed since {failed_since.isoformat()}.")
    return failed_analyses
