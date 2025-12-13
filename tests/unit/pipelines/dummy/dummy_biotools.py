from bridge.core.biotools import (
    BiotoolsIdType,
    UrlftpType,
    VersionType,
    License as BioToolsLicense,
    TopicItem,
    FunctionItem,
    ToolTypeEnum,
    LanguageEnum,
)


class DummyBioToolsTool:
    """
    Minimal dummy for a bio.tools ToolModel-like object,
    shaped like the real generated Pydantic models.
    """

    def __init__(self):
        # RootModels in the real schema
        self.biotoolsID = BiotoolsIdType(root="tool-name")
        self.homepage = UrlftpType(root="https://example.org")

        # Plain fields
        self.name = "tool-name"
        self.description = "Existing tool description"

        # License is an enum member (NOT a list)
        self.license = BioToolsLicense.MIT

        # version is a list of VersionType RootModels (NOT a plain string)
        self.version = [VersionType(root="1.2.3")]

        # language is a list of LanguageEnum
        self.language = [LanguageEnum.Python]

        # toolType is a list of ToolTypeEnum (needed by readme mapping)
        self.toolType = [ToolTypeEnum.Command_line_tool]

        # topic is a list of TopicItem (needed by topics mapping)
        self.topic = [TopicItem(term="Genomics", uri="http://edamontology.org/topic_0622")]

        # function is a list[FunctionItem] or None. If your mapper uses it, include a minimal stub.
        # If not used, leaving None is fine.
        self.function = None

        # link is list of LinkItem in real model; your mapper might use it elsewhere.
        # If MapBioTools2GitHub doesn't use it, keep minimal / None.
        self.link = None

        # fields used by other pipelines (kept from your earlier dummy)
        self.documentation = None
        self.maturity = None
        self.publication = None
