# CRIMan Help

CRIMan is calibration and service record management system.

---

## 🏠 Home

Displays all active service records sorted by **Next Service Date** (soonest first).
Use this view to quickly identify gauges approaching or past their service due date.

---

## ➕ Add Tool

A three-step wizard for registering a new gauge and its initial service record in one flow.

1. **Manufacturer** — Select an existing manufacturer or create a new one.
2. **Model** — Select an existing model for that manufacturer or add a new model with size details.
3. **Service** — Set the location, gauge number, calibrated-by user, certificate number, service dates, and post-condition.

The certificate number is auto-incremented. Check **Override** to enter a custom value.

---

## 🔩 Equipment

### Manufacturers

Manage the list of gauge manufacturers. Each manufacturer has a name and description.
Models are linked to a manufacturer, so add manufacturers before adding models.

### Models

Manage gauge models. Each model belongs to a manufacturer and includes a name, size range (Size / End Size), and description.
Service records reference a model directly.

### Service

The central record of all calibration activity. Each service record captures:
manufacturer, model, location, gauge serial number, technician, calibration date,
certificate number, last/next service dates, and post-condition (*New, Good, Poor, Bad*).

Records marked **Bad** are excluded from standard exports but included in the Damaged Units export.

---

## ⚙️ Administration

### Locations

Manage facility locations (e.g. CRM, CRI, NGHT). Locations are assigned to service records
and to users. Default locations are seeded on first run.

### Users

Manage calibration technicians. Each user has a name and an assigned location.
Users are selected as the "Calibrated By" person when creating or editing service records.

---

## 📊 Data

### Export

Four export options are available:

| Export | Contents |
|---|---|
| Full Export | All active service records plus the models list |
| Service Only | Active service records (condition is not Bad) |
| Damaged Units | Service records with condition = Bad |
| Backup | Raw export of all tables for archival |

All exports are formatted Excel (.xlsx) files with styled headers and auto-sized columns.

### Import

Download the import template (`CRIMan_Import.xlsx`), fill in the sheets
(Manufacturers, Models, Locations, Users, Service), then upload the file.
Rows with matching IDs are updated; new IDs are inserted. Blank rows are skipped.

### Schedule

Create scheduled report recipients. Each schedule has a name, description, email address,
and a cron expression defining when it runs. Click **Run Scheduler** to immediately send
the current service report to all configured recipients as an Excel attachment.

---

## Tips

- Click any column header to sort the table by that column. Click again to reverse.
- Add manufacturers and locations before adding models or users.
- Certificate numbers are auto-incremented (0001, 0002 …). Use Override only when assigning a specific number.
- Use the Import template to bulk-load data into a fresh installation.
- Records with condition **Bad** remain in the database but are hidden from the home view and standard exports.
