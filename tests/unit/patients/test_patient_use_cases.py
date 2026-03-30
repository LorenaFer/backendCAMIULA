import pytest

from app.core.exceptions import AppException, ConflictException, NotFoundException
from app.modules.patients.application.dtos.patient_dto import (
    CreatePatientDTO,
    GetPatientHistoryDTO,
    SearchPatientDTO,
)
from app.modules.patients.application.use_cases.create_patient import (
    CreatePatient,
    normalize_relacion_univ,
)
from app.modules.patients.application.use_cases.get_patient_history import (
    GetPatientHistory,
)
from app.modules.patients.application.use_cases.search_patient import SearchPatient
from app.modules.patients.domain.entities.patient import Patient, PatientHistoryEntry


class FakePatientRepo:
    def __init__(self):
        self.by_cedula = {}
        self.by_nhm = {}
        self.by_id = {}
        self.history = {}
        self.next_nhm = 100001

    async def find_by_cedula(self, cedula: str):
        return self.by_cedula.get(cedula)

    async def find_by_nhm(self, nhm: int):
        return self.by_nhm.get(nhm)

    async def find_by_id(self, patient_id: str):
        return self.by_id.get(patient_id)

    async def get_next_nhm(self):
        return self.next_nhm

    async def create(self, data: dict, created_by: str):
        patient = Patient(
            id="p-1",
            nhm=data["nhm"],
            cedula=data["cedula"],
            nombre=data["nombre"],
            apellido=data["apellido"],
            relacion_univ=data["relacion_univ"],
            es_nuevo=data["es_nuevo"],
            datos_medicos=data["datos_medicos"],
            contacto_emergencia=data["contacto_emergencia"],
        )
        self.by_cedula[patient.cedula] = patient
        self.by_nhm[patient.nhm] = patient
        self.by_id[patient.id] = patient
        return patient

    async def list_history(self, patient_id: str, limit: int, exclude_appointment_id):
        entries = self.history.get(patient_id, [])
        return entries[:limit]


def test_normalize_relacion_univ_from_ula_codes():
    assert normalize_relacion_univ("E") == "empleado"
    assert normalize_relacion_univ("P") == "profesor"
    assert normalize_relacion_univ("B") == "estudiante"
    assert normalize_relacion_univ("X") == "tercero"


@pytest.mark.asyncio
async def test_create_patient_applies_defaults_and_mapping():
    repo = FakePatientRepo()
    use_case = CreatePatient(repo)

    patient = await use_case.execute(
        CreatePatientDTO(
            cedula="V-12345678",
            nombre="Pedro",
            apellido="Gonzalez",
            relacion_univ="E",
        ),
        created_by="u-1",
    )

    assert patient.nhm == 100001
    assert patient.relacion_univ == "empleado"
    assert patient.es_nuevo is True


@pytest.mark.asyncio
async def test_create_patient_rejects_duplicate_cedula():
    repo = FakePatientRepo()
    repo.by_cedula["V-111"] = Patient(
        id="p-x",
        nhm=100010,
        cedula="V-111",
        nombre="A",
        apellido="B",
    )

    use_case = CreatePatient(repo)
    with pytest.raises(ConflictException):
        await use_case.execute(
            CreatePatientDTO(cedula="V-111", nombre="Nuevo", apellido="Paciente"),
            created_by="u-1",
        )


@pytest.mark.asyncio
async def test_search_requires_exactly_one_query_param():
    repo = FakePatientRepo()
    use_case = SearchPatient(repo)

    with pytest.raises(AppException):
        await use_case.execute(SearchPatientDTO())

    with pytest.raises(AppException):
        await use_case.execute(SearchPatientDTO(cedula="V-1", nhm=100001))


@pytest.mark.asyncio
async def test_search_by_cedula_success():
    repo = FakePatientRepo()
    p = Patient(id="p-1", nhm=100001, cedula="V-123", nombre="N", apellido="A")
    repo.by_cedula[p.cedula] = p

    use_case = SearchPatient(repo)
    found = await use_case.execute(SearchPatientDTO(cedula="V-123"))
    assert found.id == "p-1"


@pytest.mark.asyncio
async def test_history_requires_existing_patient():
    repo = FakePatientRepo()
    use_case = GetPatientHistory(repo)

    with pytest.raises(NotFoundException):
        await use_case.execute(GetPatientHistoryDTO(patient_id="missing"))


@pytest.mark.asyncio
async def test_history_returns_entries_when_patient_exists():
    repo = FakePatientRepo()
    patient = Patient(id="p-1", nhm=100001, cedula="V-1", nombre="N", apellido="A")
    repo.by_id[patient.id] = patient
    repo.history[patient.id] = [
        PatientHistoryEntry(
            id="h-1",
            fecha="2026-03-21",
            especialidad="Medicina General",
            doctor_nombre="Dr. X",
            diagnostico_descripcion="Cefalea",
            diagnostico_cie10="R51",
        )
    ]

    use_case = GetPatientHistory(repo)
    data = await use_case.execute(GetPatientHistoryDTO(patient_id=patient.id, limit=5))
    assert len(data) == 1
    assert data[0].id == "h-1"
