# Modulo: Portal del Paciente

Endpoints usados por el flujo publico del paciente (login sin contrasena, registro, hub).

---

## Flujo

1. Paciente ingresa cedula o NHM en `/portal`
2. `POST /auth/patient/login` → verifica si existe
3. Si `found: true` → redirige a hub del paciente
4. Si `found: false` → redirige a registro (`POST /patients/register`)

---

## Endpoints Utilizados

### 1. `POST /auth/patient/login` — Login por cedula/NHM

Ver [01-auth.md](./01-auth.md#3-post-authpatientlogin)

### 2. `POST /patients/register` — Registro desde portal

Ver [02-patients.md](./02-patients.md#3-post-patientsregister)

### 3. `GET /appointments?fk_patient_id={id}` — Citas del paciente

Ver [03-appointments.md](./03-appointments.md)

### 4. `GET /medical-records/patient/{patient_id}` — Historial

Ver [05-medical-records.md](./05-medical-records.md#5-get-medical-recordspatientpatient_id--historial-del-paciente)
