"""Reports routes: POST /api/reports, GET /api/reports (Sprint 2.3)."""

from fastapi import APIRouter, status

from app.models.report import Report, ReportCreate, ReportList
from app.services.reports import list_reports, save_report

router = APIRouter()


@router.post("/reports", response_model=Report, status_code=status.HTTP_201_CREATED)
def create_report(data: ReportCreate) -> Report:
    return save_report(data)


@router.get("/reports", response_model=ReportList)
def get_reports(stream_id: str = "") -> ReportList:
    reports = list_reports(stream_id)
    return ReportList(reports=reports, count=len(reports))
