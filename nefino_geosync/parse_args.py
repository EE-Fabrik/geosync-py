import argparse

def parse_args(cached=[]):
    if len(cached) > 0:
        return cached[0]
    parser = argparse.ArgumentParser(
        prog="Nefino GeoSync",
        description='Download available geodata from the Nefino API.',
        epilog='If you have further questions please reach out to us! The maintainers for this tool can be found on https://github.com/nefino/geosync-py.')
    parser.add_argument('-c', '--configure', action='store_true', help='Edit your existing configuration. The first-run wizard will be shown again, with your existing configuration pre-filled.')
    parser.add_argument('-r', '--resume', action='store_true', help='Resume checking for completed analyses and downloading them. This will skip the analysis start step.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print more information to the console.')
    parser.add_argument('-s', '--skip-unfinished', action='store_true', help='Skip waiting for unfinished analyses to complete.')
    parser.add_argument('-a', '--app-dir', required=False, help='The directory where the application data is stored.')
    parser.add_argument('-fs', '--federal-states', nargs='+', required=False, help='List of federal states as NUTS:DE codes (see https://de.wikipedia.org/wiki/NUTS:DE).')
    parser.add_argument('-n', '--non-interactive', action='store_true', help='Run the script in non-interactive mode. This will raise exceptions instead of pretty-printing them to the terminal, among other things. Should be used when running as an automated job.')
    args = parser.parse_args()
    cached.append(args)
    return args