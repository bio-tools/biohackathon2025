class DummyGitHubRepoModel:
    """
    Minimal dummy for `GitHubRepoModel` with the attributes the mapper uses.
    """

    class Release:
        def __init__(self, tag_name: str):
            self.tag_name = tag_name

    class License:
        def __init__(self, spdx_id: str):
            self.spdx_id = spdx_id

    class CodeOfConduct:
        def __init__(self, html_url: str | None):
            self.html_url = html_url

    class FullRepo:
        def __init__(self):
            self.name = "repo-name"
            self.html_url = "https://github.com/example/repo"
            self.homepage = "https://example.org/home"
            self.license = DummyGitHubRepoModel.License("MIT")

            # documentation mapping inputs
            self.has_wiki = True
            self.code_of_conduct = DummyGitHubRepoModel.CodeOfConduct(
                "https://github.com/example/repo/blob/main/CODE_OF_CONDUCT.md"
            )

            # description mapping inputs
            self.description = "Short repo description"

            # maturity mapping inputs
            self.stargazers_count = 10
            self.forks_count = 2
            self.watchers_count = 3
            self.subscribers_count = 1
            self.archived = False

            # (kept from your earlier dummy)
            self.topics = ["genomics"]
            self.language = "Python"  # not used by MapGitHub2BioTools.map, but fine

    def __init__(self):
        self.repo = DummyGitHubRepoModel.FullRepo()

        # MapGitHub2BioTools expects repo.languages (plural)
        self.languages = ["Python"]

        # MapGitHub2BioTools expects latest_release.tag_name
        self.latest_release = DummyGitHubRepoModel.Release("1.2.3")

        # MapGitHub2BioTools expects repo.readme
        self.readme = "README contents"

        # MapGitHub2BioTools expects repo.github_pages
        self.github_pages = None
