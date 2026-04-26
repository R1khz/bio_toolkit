from bio_toolkit.contracts.common.models import ContractModel
from bio_toolkit.contracts.doctor.models import DiagnosticRow


class DoctorResponse(ContractModel):
    rows: list[DiagnosticRow]
    warnings: list[str]
