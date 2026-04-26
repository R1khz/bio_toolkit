from bio_toolkit.contracts.common.models import ContractModel


class DiagnosticRow(ContractModel):
    setting: str
    value: str
    status: str
