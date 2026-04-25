from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProviderRef(ContractModel):
    name: str


class SourceRef(ContractModel):
    kind: str
    label: str
    accession: str | None = None
    database: str | None = None
    provider: str | None = None
    rettype: str | None = None


class ExportArtifact(ContractModel):
    format: str
    path: str


class WarningItem(ContractModel):
    code: str
    message: str
