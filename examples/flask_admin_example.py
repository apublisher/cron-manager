# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportUntypedFunctionDecorator=false, reportUnusedFunction=false
from flask import Blueprint, current_app, jsonify, request

from cron_manager import FlaskCronService

cron_admin = Blueprint("cron_admin", __name__, url_prefix="/admin/cron")


def _service() -> FlaskCronService:
    return FlaskCronService.from_config(current_app.config)


@cron_admin.get("/")
def list_jobs():
    payload, status_code = _service().list_jobs_response()
    return jsonify(payload), status_code


@cron_admin.get("/<string:job_id>/exists")
def exists(job_id: str):
    payload, status_code = _service().exists_response(job_id)
    return jsonify(payload), status_code


@cron_admin.put("/<string:job_id>")
def upsert(job_id: str):
    data = request.get_json(silent=True) or {}
    payload, status_code = _service().upsert_response(
        job_id=job_id,
        schedule=str(data.get("schedule", "")),
        command=str(data.get("command", "")),
        enabled=bool(data.get("enabled", True)),
    )
    return jsonify(payload), status_code


@cron_admin.post("/<string:job_id>/pause")
def pause(job_id: str):
    payload, status_code = _service().pause_response(job_id)
    return jsonify(payload), status_code


@cron_admin.post("/<string:job_id>/resume")
def resume(job_id: str):
    payload, status_code = _service().resume_response(job_id)
    return jsonify(payload), status_code


@cron_admin.delete("/<string:job_id>")
def delete(job_id: str):
    payload, status_code = _service().delete_response(job_id)
    return jsonify(payload), status_code
