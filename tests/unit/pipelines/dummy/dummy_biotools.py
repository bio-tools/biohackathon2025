class DummyBioToolsTool:
    """
    Minimal dummy for a bio.tools `ToolModel`-like object with attributes used by mappers.
    """

    class LinkElem:
        def __init__(self, url: str):
            self.url = url

    def __init__(self):
        self.biotoolsID = "tool-name"
        self.name = "tool-name"
        self.homepage = "https://example.org"

        self.language = ["Python"]
        self.license = ["MIT"]
        self.version = "1.2.3"

        self.link = [
            DummyBioToolsTool.LinkElem("https://tool.com/a"),
            DummyBioToolsTool.LinkElem("https://tool.com/b"),
        ]

        # fields used by MapGitHub2BioTools.map
        self.documentation = None
        self.description = "Existing tool description"
        self.maturity = None
        self.publication = None
