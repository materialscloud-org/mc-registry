# -*- coding: utf-8 -*-
import os
import re
from dataclasses import dataclass
from dataclasses import replace
from urllib.parse import urlsplit
from urllib.parse import urlunsplit

from repo2env import Environment
from repo2env import fetch_from_url
from repo2env.git_util import GitRepo


@dataclass
class Release:
    environment: Environment
    url: str


RELEASE_LINE_PATTERN = r"^(?P<rev>[^:]*?)(:(?P<rev_selection>.*))?$"


def _split_release_line(url):
    parsed_url = urlsplit(url)
    if "@" in parsed_url.path:
        path, release_line = parsed_url.path.rsplit("@", 1)
        return urlunsplit(parsed_url._replace(path=path)), release_line
    return url, None


def _get_release_commits(repo, release_line):
    match = re.match(RELEASE_LINE_PATTERN, release_line)

    if not match:
        raise ValueError(f"Invalid release line specification: {release_line}")

    rev = match.groupdict()["rev"] or repo.get_current_branch()

    if match.groupdict()["rev_selection"] is None:
        # No rev_selection means to select this and only this specific
        # revision.  For example: '@main' means, simply checkout 'main' (could
        # be a branch or a tag, however branches have priority).
        for ref in [
            f"refs/heads/{rev}",
            f"refs/remotes/origin/{rev}",
            f"refs/tags/{rev}",
        ]:
            if ref.encode() in repo.refs:
                yield rev, repo.get_peeled(ref.encode()).decode()
                return
        # rev likely committish (commit)
        yield rev, rev

    elif match.groupdict()["rev_selection"]:
        # A rev selection is provided, we fetch the full rev list for the given
        # selection.  For example: '@main:v1..v2' means all commits from v1
        # (exclusive) to v2 (inclusive).
        selected_commits = repo.rev_list(match.groupdict()["rev_selection"])
        for tag in repo.get_merged_tags(rev):
            commit = repo.get_commit_for_tag(tag)
            if commit in selected_commits:
                yield tag, commit

    else:
        # The rev selection is empty, select all tagged commits for the
        # selected revision.  For example: '@main:' means all tagged commits on
        # the main branch.
        for tag in repo.get_merged_tags(rev):
            yield tag, repo.get_commit_for_tag(tag)


def _gather_releases(release_specs, scan_environment):
    for release_spec in release_specs:
        if isinstance(release_spec, str):
            url = release_spec
            environment_override = None
            version_override = None
        else:
            url = release_spec["url"]
            environment_override = release_spec.get("environment")
            version_override = release_spec.get("version")

        def _set_overrides(version, release):
            return version_override or version, replace(
                release, environment=environment_override or release.environment
            )

        # The way that an app is retrieved is determined by the scheme of the
        # release url.  For example, "git+https://example.com/my-app.git" means
        # that the app is located at a remote git repository from which it can
        # be downloaded (cloned) via https.
        base_url, release_line = _split_release_line(url)
        parsed_url = urlsplit(base_url)

        with fetch_from_url(base_url) as repo_path:
            if parsed_url.scheme.startswith("git+"):
                repo = GitRepo(os.fspath(repo_path))
                for ref, sha in _get_release_commits(
                    repo, release_line or repo.get_current_branch()
                ):
                    # Parse environment from local copy of repository.
                    environment = scan_environment(
                        f"git+file:{os.fspath(repo_path.resolve())}@{sha}"
                    )
                    # Replace release specifier to point to specific commit.
                    path = f"{parsed_url.path.rsplit('@', 1)[0]}@{sha}"
                    release = Release(
                        url=urlunsplit(parsed_url._replace(path=path)),
                        environment=environment,
                    )
                    yield _set_overrides(ref, release)
            else:
                release = Release(
                    url=url,
                    environment=scan_environment(
                        f"file:{os.fspath(repo_path.resolve())}"
                    ),
                )
                yield _set_overrides(None, release)


def gather_releases(app_data, scan_environment):
    for version, release in _gather_releases(
        app_data.get("releases", []), scan_environment
    ):
        if version is None:
            raise ValueError(f"Unable to determine version for: {release}")
        yield version, release
