import logging
from typing import Any, Optional, List
from .api_client import general_availability_operation, local_availability_operation, start_analyses_operation
from .compose_requests import compose_complete_requests
from .journal import Journal
from .graphql_errors import check_errors
from .parse_args import parse_args
from sgqlc.endpoint.http import HTTPEndpoint

AnalysesMutationResult = Any


log = logging.getLogger(__name__)

def get_non_downloaded_analyses(journal, federal_state_key) -> List[str]:
    return [pk for pk, federal_state in journal.analysis_states.items() if federal_state == federal_state_key and pk not in journal.synced_analyses]


def start_analyses(client: HTTPEndpoint) -> Optional[AnalysesMutationResult]:
    """Starts the analyses for all updated data."""
    journal = Journal.singleton()
    args = parse_args()
    # Get information about our permissions and the general availability of layers
    general_op = general_availability_operation()
    log.info("Checking for layers to update...")
    general_data = client(general_op)
    check_errors(general_data)
    general_availability = (general_op + general_data)

    # Get information about the availability of layers in specific areas
    local_op = local_availability_operation(general_availability)
    local_data = client(local_op)
    check_errors(local_data)
    local_availability = (local_op + local_data)

    # Start the analyses
    analysis_inputs = compose_complete_requests(general_availability, local_availability)
    if len(analysis_inputs) == 0:
        # We can only check for layer having been unpacked already.
        # So if we're here, we've already unpacked all latest layers.
        log.info("✅ No layers to update. Done.")
        return None

    if args.federal_states:
        analysis_inputs = {fs_key:val for fs_key, val in analysis_inputs.items() if fs_key in args.federal_states}

    analyses = None

    # Info: In manchen Bundesländern sind in den heruntergeladenen ZipFiles für DE1 sind keine Layer enthalten, so dass immer wieder neue Analysen angestoßen werden.
    # Das soll demnächst gefixt werden, so dass zumindest leere Geopackages ausgeliefert werden.
    # TODO (minor) There might already be a PENDING/RUNNING analysis that has not been downloaded yet. Skip analysis if that is the case.
    for federal_state_key in analysis_inputs:
        non_downloaded_analyses = get_non_downloaded_analyses(journal, federal_state_key)
        if non_downloaded_analyses:
            log.info(f"The following existing analyses for federal state {federal_state_key} have not been downloaded yet, skipping analysis.")
        else:
            log.info(f"Starting analysis for {federal_state_key} for the following clusters/layers:")
            for request in analysis_inputs[federal_state_key].specs.requests:
                layers = [l.layer_name for l in request.layers]
                log.info(f"- Cluster: {request.cluster_name}, layers: {layers}")
            analyses_op = start_analyses_operation({federal_state_key: analysis_inputs[federal_state_key]})
            analyses_data = client(analyses_op)
            check_errors(analyses_data)
            analyses = (analyses_op + analyses_data)

            # Add the analyses to the journal
            journal.record_analyses_requested(analyses)

    return(analyses)