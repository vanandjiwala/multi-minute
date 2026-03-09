import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlmodel import Session

from app.config import settings
from app.database import get_session
from app.models.script import Script
from app.repositories.base import AbstractScriptRepository
from app.repositories.script_repository import SQLModelScriptRepository
from app.schemas.script import ScriptListItem, ScriptRead, ValidationResult as ValidationResultSchema
from app.services.validator import validate_script

router = APIRouter(prefix="/scripts", tags=["scripts"])


def get_repo(session: Annotated[Session, Depends(get_session)]) -> AbstractScriptRepository:
    return SQLModelScriptRepository(session)


@router.post("", response_model=ScriptRead, status_code=status.HTTP_201_CREATED)
def upload_script(
    script_file: Annotated[UploadFile, File(description="The .py script file")],
    requirements_file: Annotated[UploadFile | None, File(description="Optional requirements.txt")] = None,
    repo: AbstractScriptRepository = Depends(get_repo),
):
    name = script_file.filename or "script.py"
    script = Script(name=name)
    script = repo.create(script)

    script_dir = Path(settings.scripts_path) / script.id
    script_dir.mkdir(parents=True, exist_ok=True)

    with open(script_dir / "script.py", "wb") as f:
        f.write(script_file.file.read())

    if requirements_file is not None:
        with open(script_dir / "requirements.txt", "wb") as f:
            f.write(requirements_file.file.read())
        script.has_requirements = True
        script = repo.update(script)

    return script


@router.get("", response_model=list[ScriptListItem])
def list_scripts(repo: AbstractScriptRepository = Depends(get_repo)):
    return repo.list_all()


@router.get("/{script_id}", response_model=ScriptRead)
def get_script(script_id: str, repo: AbstractScriptRepository = Depends(get_repo)):
    script = repo.get_by_id(script_id)
    if script is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")
    return script


@router.put("/{script_id}", response_model=ScriptRead)
def update_script(
    script_id: str,
    script_file: Annotated[UploadFile | None, File(description="Replacement .py script")] = None,
    requirements_file: Annotated[UploadFile | None, File(description="Replacement requirements.txt")] = None,
    repo: AbstractScriptRepository = Depends(get_repo),
):
    script = repo.get_by_id(script_id)
    if script is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")

    script_dir = Path(settings.scripts_path) / script_id

    if script_file is not None:
        script_dir.mkdir(parents=True, exist_ok=True)
        with open(script_dir / "script.py", "wb") as f:
            f.write(script_file.file.read())
        script.name = script_file.filename or script.name

    if requirements_file is not None:
        script_dir.mkdir(parents=True, exist_ok=True)
        with open(script_dir / "requirements.txt", "wb") as f:
            f.write(requirements_file.file.read())
        script.has_requirements = True

    script.updated_at = datetime.now(timezone.utc)
    return repo.update(script)


@router.post("/{script_id}/validate", response_model=ValidationResultSchema)
def validate_script_endpoint(
    script_id: str,
    repo: AbstractScriptRepository = Depends(get_repo),
):
    script = repo.get_by_id(script_id)
    if script is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")

    script_path = Path(settings.scripts_path) / script_id / "script.py"
    if not script_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script file not found on disk")

    result = validate_script(script_path)
    return ValidationResultSchema(
        valid=result.valid,
        syntax_ok=result.syntax_ok,
        syntax_error=result.syntax_error,
    )


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_script(script_id: str, repo: AbstractScriptRepository = Depends(get_repo)):
    deleted = repo.delete(script_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Script not found")

    script_dir = Path(settings.scripts_path) / script_id
    if script_dir.exists():
        shutil.rmtree(script_dir)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
