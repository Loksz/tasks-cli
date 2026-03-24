"""Tests de CLI usando typer.testing.CliRunner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from tasks_cli.cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirige db_path y config a directorios temporales para cada test."""
    tasks_dir = tmp_path / ".tasks"
    tasks_dir.mkdir()

    # Parchamos get_config para que use la DB temporal
    from tasks_cli.models.task import Config, Priority

    fake_cfg = Config(
        device_id="test-device",
        db_path=tasks_dir / "tasks.db",
        default_priority=Priority.medium,
    )

    monkeypatch.setattr("tasks_cli.cli.tasks.get_config", lambda: fake_cfg)
    monkeypatch.setattr("tasks_cli.cli.main.get_config", lambda: fake_cfg)

    # Evitamos escrituras de caché de autocompletado
    monkeypatch.setattr("tasks_cli.cache.update", lambda repo: None)


# ---------------------------------------------------------------------------
# tasks add
# ---------------------------------------------------------------------------


class TestAddCommand:
    def test_add_basic(self) -> None:
        result = runner.invoke(app, ["add", "Mi primera tarea"])
        assert result.exit_code == 0
        assert "Mi primera tarea" in result.output

    def test_add_with_priority(self) -> None:
        result = runner.invoke(app, ["add", "Tarea urgente", "--priority", "high"])
        assert result.exit_code == 0

    def test_add_with_project_and_tag(self) -> None:
        result = runner.invoke(app, ["add", "Tarea", "--project", "backend", "--tag", "python"])
        assert result.exit_code == 0

    def test_add_quiet_returns_only_id(self) -> None:
        result = runner.invoke(app, ["add", "Silenciosa", "--quiet"])
        assert result.exit_code == 0
        output = result.output.strip()
        # Debe ser un UUID (36 caracteres)
        assert len(output) == 36

    def test_add_empty_title_fails(self) -> None:
        result = runner.invoke(app, ["add", "   "])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# tasks list
# ---------------------------------------------------------------------------


class TestListCommand:
    def test_list_empty(self) -> None:
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No hay tareas" in result.output

    def test_list_shows_added_task(self) -> None:
        runner.invoke(app, ["add", "Tarea listable"])
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Tarea listable" in result.output

    def test_list_format_json(self) -> None:
        runner.invoke(app, ["add", "JSON tarea", "--quiet"])
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0
        import json
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert any(t["title"] == "JSON tarea" for t in data)

    def test_list_format_ids(self) -> None:
        id_result = runner.invoke(app, ["add", "IDs tarea", "--quiet"])
        task_id = id_result.output.strip()
        result = runner.invoke(app, ["list", "--format", "ids"])
        assert task_id in result.output

    def test_list_filter_by_status(self) -> None:
        runner.invoke(app, ["add", "Pendiente"])
        result = runner.invoke(app, ["list", "--status", "pending"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# tasks done
# ---------------------------------------------------------------------------


class TestDoneCommand:
    def test_done_marks_task_completed(self) -> None:
        id_result = runner.invoke(app, ["add", "Completar esto", "--quiet"])
        task_id = id_result.output.strip()
        result = runner.invoke(app, ["done", task_id])
        assert result.exit_code == 0
        assert "completada" in result.output.lower()

    def test_done_invalid_id_shows_error(self) -> None:
        result = runner.invoke(app, ["done", "00000000"])
        assert result.exit_code == 0  # typer no fuerza exit != 0 en continue
        assert "no encontrada" in result.output.lower()


# ---------------------------------------------------------------------------
# tasks edit
# ---------------------------------------------------------------------------


class TestEditCommand:
    def test_edit_title(self) -> None:
        id_result = runner.invoke(app, ["add", "Título viejo", "--quiet"])
        task_id = id_result.output.strip()
        result = runner.invoke(app, ["edit", task_id, "--title", "Título nuevo"])
        assert result.exit_code == 0
        assert "actualizada" in result.output.lower()

    def test_edit_priority(self) -> None:
        id_result = runner.invoke(app, ["add", "Editar prioridad", "--quiet"])
        task_id = id_result.output.strip()
        result = runner.invoke(app, ["edit", task_id, "--priority", "high"])
        assert result.exit_code == 0

    def test_edit_nonexistent_task_fails(self) -> None:
        result = runner.invoke(app, ["edit", "00000000", "--title", "X"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# tasks delete
# ---------------------------------------------------------------------------


class TestDeleteCommand:
    def test_delete_with_force(self) -> None:
        id_result = runner.invoke(app, ["add", "Eliminar esta", "--quiet"])
        task_id = id_result.output.strip()
        result = runner.invoke(app, ["delete", task_id, "--force"])
        assert result.exit_code == 0
        assert "eliminada" in result.output.lower()

    def test_delete_nonexistent_fails(self) -> None:
        result = runner.invoke(app, ["delete", "00000000", "--force"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# tasks show
# ---------------------------------------------------------------------------


class TestShowCommand:
    def test_show_existing_task(self) -> None:
        id_result = runner.invoke(app, ["add", "Ver detalle", "--quiet"])
        task_id = id_result.output.strip()
        result = runner.invoke(app, ["show", task_id])
        assert result.exit_code == 0
        assert "Ver detalle" in result.output

    def test_show_nonexistent_fails(self) -> None:
        result = runner.invoke(app, ["show", "00000000"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# tasks search
# ---------------------------------------------------------------------------


class TestSearchCommand:
    def test_search_finds_by_title(self) -> None:
        runner.invoke(app, ["add", "Revisar documentación"])
        result = runner.invoke(app, ["search", "documentación"])
        assert result.exit_code == 0
        assert "Revisar documentación" in result.output

    def test_search_no_results(self) -> None:
        result = runner.invoke(app, ["search", "xyznoresults"])
        assert result.exit_code == 0
        assert "Sin resultados" in result.output


# ---------------------------------------------------------------------------
# tasks stats / today / overdue / upcoming / projects / tags
# ---------------------------------------------------------------------------


class TestViewCommands:
    def test_stats_empty(self) -> None:
        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "Total" in result.output

    def test_today_empty(self) -> None:
        result = runner.invoke(app, ["today"])
        assert result.exit_code == 0

    def test_overdue_empty(self) -> None:
        result = runner.invoke(app, ["overdue"])
        assert result.exit_code == 0

    def test_upcoming_empty(self) -> None:
        result = runner.invoke(app, ["upcoming"])
        assert result.exit_code == 0

    def test_projects_empty(self) -> None:
        result = runner.invoke(app, ["projects"])
        assert result.exit_code == 0

    def test_tags_empty(self) -> None:
        result = runner.invoke(app, ["tags"])
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# tasks config
# ---------------------------------------------------------------------------


class TestConfigCommand:
    def test_config_get_all(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from tasks_cli.models.task import Config

        cfg = Config(device_id="dev-1", db_path=tmp_path / "tasks.db")
        monkeypatch.setattr("tasks_cli.cli.main.get_config", lambda: cfg)
        result = runner.invoke(app, ["config", "get"])
        assert result.exit_code == 0
        assert "device_id" in result.output

    def test_config_get_unknown_key_fails(self) -> None:
        result = runner.invoke(app, ["config", "get", "clave_inexistente"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# tasks export / import
# ---------------------------------------------------------------------------


class TestExportImportCommands:
    def test_export_json(self, tmp_path: Path) -> None:
        runner.invoke(app, ["add", "Exportar esta"])
        out_file = str(tmp_path / "out.json")
        result = runner.invoke(app, ["export", "--format", "json", "--output", out_file])
        assert result.exit_code == 0
        assert Path(out_file).exists()

    def test_export_csv(self, tmp_path: Path) -> None:
        runner.invoke(app, ["add", "CSV tarea"])
        out_file = str(tmp_path / "out.csv")
        result = runner.invoke(app, ["export", "--format", "csv", "--output", out_file])
        assert result.exit_code == 0

    def test_export_markdown(self, tmp_path: Path) -> None:
        runner.invoke(app, ["add", "MD tarea"])
        out_file = str(tmp_path / "out.md")
        result = runner.invoke(app, ["export", "--format", "markdown", "--output", out_file])
        assert result.exit_code == 0

    def test_import_json(self, tmp_path: Path) -> None:
        import json
        from datetime import datetime, timezone

        tasks_data = [{
            "id": "aaaaaaaa-0000-0000-0000-000000000001",
            "title": "Importada",
            "notes": None,
            "status": "pending",
            "priority": "medium",
            "project": None,
            "tags": [],
            "due_date": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "sync_status": "local",
            "sync_version": 0,
            "device_id": "test",
        }]
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps(tasks_data), encoding="utf-8")

        result = runner.invoke(app, ["import", "--file", str(import_file)])
        assert result.exit_code == 0
        assert "Importadas: 1" in result.output
