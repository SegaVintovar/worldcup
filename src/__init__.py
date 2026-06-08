from .gui.nice_one import prediction
from .pages.header import header
from .pages.fixtures import matches
from .results.football_api import get_worldcup_matches

all = [prediction, header, matches, get_worldcup_matches]
