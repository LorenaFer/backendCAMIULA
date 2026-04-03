# Modulo: Dashboard BI

Endpoint consolidado que retorna todas las metricas pre-calculadas del servidor.

---

## `GET /dashboard`

**Auth:** JWT requerido

**Query Params:**

| Param | Tipo | Default | Descripcion |
|-------|------|---------|-------------|
| `fecha` | string | Hoy | Fecha de referencia (YYYY-MM-DD) |
| `periodo` | string | `day` | `day` \| `week` \| `month` \| `year` |

**Response:**

```typescript
interface DashboardResponse {
  fecha: string;
  generated_at: string;

  // KPIs ejecutivos
  kpis: {
    total_appointments: number;
    appointments_today: number;
    pending_appointments: number;
    attendance_rate: number;         // %
    no_show_rate: number;            // %
    cancellation_rate: number;       // %
    total_patients: number;
    new_patients: number;
    total_doctors: number;
    inventory_value: number;         // Bs
  };

  // Charts data
  appointments_by_status: Record<string, number>;
  appointments_by_specialty: { name: string; count: number }[];
  daily_trend: number[];
  hourly_distribution: { hour: string; count: number }[];
  heatmap: number[][];               // 7 dias x 24 horas
  occupancy_by_specialty: {
    name: string;
    available_slots: number;
    booked: number;
  }[];
  absenteeism_by_specialty: {
    name: string;
    total: number;
    no_shows: number;
    rate: number;
  }[];
  performance_by_doctor: {
    name: string;
    specialty: string;
    count: number;
    attended: number;
  }[];

  // Demograficos
  patients_by_type: Record<string, number>;
  patients_by_sex: Record<string, number>;
  first_time_count: number;
  returning_count: number;

  // Diagnosticos
  top_diagnoses: {
    code: string;
    description: string;
    count: number;
  }[];

  // Inventario
  inventory: {
    total_medications: number;
    critical_stock: number;
    expiring_batches: number;
    estimated_value: number;
  };
  top_consumption: {
    medication_id: string;
    generic_name: string;
    total_dispatched: number;
    patient_count: number;
  }[];
}
```

Este unico endpoint reemplaza ~10 llamadas paralelas que el frontend hacia antes.
Todas las agregaciones se ejecutan en el servidor en <50ms (ver benchmarks).
