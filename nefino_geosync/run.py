"""This is the main entry point of the application."""
import logging
import os
import sys

from .api_client import get_client
from .start_analyses import start_analyses
from .download_completed_analyses import download_completed_analyses
from .config import Config
from .parse_args import parse_args


log = logging.getLogger(__name__)


def main():
    args = parse_args()

    if args.configure:
        config = Config.singleton()
        # if you are running with --configure on the first run (you don't need to)
        # you will be prompted to configure the app by the config singleton init.
        # In that case, don't prompt the user again.
        if not config.already_prompted:
            config.run_config_prompts()

    client = get_client(api_host=os.getenv("NEFINO_API_HOST", default="https://api.nefino.li"))

    if not args.resume:
        start_analyses(client)
    analyses_complete = download_completed_analyses(client)
    if analyses_complete:
        log.info("✅ All analyses have been downloaded.")
        sys.exit(0)
    else:
        log.warning("⚠️ Some analyses haven not yet finished. Please run the script again later.")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    main()