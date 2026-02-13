from bridge.core.biotools import (
    BiotoolsIdType,
    UrlftpType,
    VersionType,
    License as BioToolsLicense,
    TopicItem,
    FunctionItem,
    OperationItem,
    ToolTypeEnum,
    LanguageEnum,
    LinkItem,
    TypeEnum,
)


from pydantic import BaseModel


class DummyBioToolsTool(BaseModel):
    biotoolsID: BiotoolsIdType
    homepage: UrlftpType
    name: str
    description: str
    license: BioToolsLicense
    version: list[VersionType]
    language: list[LanguageEnum]
    toolType: list[ToolTypeEnum]
    topic: list[TopicItem]
    function: list[FunctionItem] | None
    documentation: None = None
    maturity: None = None
    publication: None = None
    link: list[LinkItem]

    def __init__(self):
        super().__init__(
            biotoolsID=BiotoolsIdType(root="tool-name"),
            homepage=UrlftpType(root="https://example.org"),
            name="tool-name",
            description="Existing tool description",
            license=BioToolsLicense.MIT,
            version=[VersionType(root="1.2.3")],
            language=[LanguageEnum.Python],
            toolType=[ToolTypeEnum.Command_line_tool],
            topic=[TopicItem(term="Genomics", uri="http://edamontology.org/topic_0622")],
            function=[
                FunctionItem(
                    operation=[
                        OperationItem(
                            term="Multiple sequence alignment",
                            uri="http://edamontology.org/operation_0492",
                        )
                    ]
                )
            ],
            link=[
                LinkItem(url=UrlftpType(root="https://tool.com/a"), type=[TypeEnum.Repository]),
                LinkItem(url=UrlftpType(root="https://tool.com/b"), type=[TypeEnum.Repository]),
            ],
        )
