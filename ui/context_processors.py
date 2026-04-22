import os

from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError

from tculink import VERSION

commit_hash = os.environ.get("OPENCARWINGS_COMMIT_SHA", "unknown")
try:
    repo = Repo(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    commit_hash = repo.git.rev_parse("HEAD")
except (InvalidGitRepositoryError, NoSuchPathError, ValueError):
    pass


def load_ver_info(request):
    return {'appinfo': {"version": VERSION, "commit": commit_hash[:7]}}