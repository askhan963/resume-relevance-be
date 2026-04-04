from fastcrud import FastCRUD

from ..models.report import Report
from ..schemas.report import ReportCreateInternal, ReportRead, ReportSummary, ReportUpdateInternal

CRUDReport = FastCRUD[
    Report,
    ReportCreateInternal,
    ReportUpdateInternal,
    ReportUpdateInternal,
    ReportRead,
    ReportSummary,
]
crud_report = CRUDReport(Report)
