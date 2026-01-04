# Auto Repair Workshop ERP

## 1. Overview

The Auto Repair Workshop ERP is a backend-focused system designed to manage the core operational processes of an automotive repair workshop. The system centralizes customer data, vehicle records, job tracking, worker assignments, and basic billing information.

The primary goal of this project is educational: to understand how real-world business processes are modeled in a backend system using **Python**, **FastAPI**, and **PostgreSQL**, without relying on heavy ORMs or full-stack ERP frameworks.

---

## 2. Project Objectives

* Model real auto-repair workshop workflows
* Implement role-based access control (Admin and Worker)
* Practice writing raw SQL with PostgreSQL
* Build a clean REST API using FastAPI
* Understand separation of concerns in backend architecture
* Prepare a foundation that can later be extended into a full ERP system

---

## 3. Technology Stack

### Backend

* **Python 3.11+**
* **FastAPI** – API framework
* **PostgreSQL** – Relational database
* **psycopg2** – PostgreSQL driver
* **JWT (JSON Web Tokens)** – Authentication

### Infrastructure

* **Docker & Docker Compose** – Local development and deployment

### Frontend (later phase)

* HTML, CSS, JavaScript (simple client or admin dashboard)

---

## 4. User Roles and Permissions

### 4.1 Admin

Admins manage system configuration and users.

Permissions:

* Create, update, and deactivate workers
* View all customers, vehicles, jobs, and invoices
* Assign workers to jobs
* Access all system data

### 4.2 Worker

Workers interact with day-to-day workshop operations.

Permissions:

* Create and update customers
* Register vehicles
* Create job cards
* Update job status
* Add job notes
* View assigned jobs

Workers cannot delete critical records or manage other users.

---

## 5. Core Business Workflow

1. Customer is registered
2. Vehicle is added to the system
3. Job card is created for the vehicle
4. Worker is assigned to the job
5. Job progresses through statuses:

   * created
   * in_progress
   * waiting_for_parts
   * completed
   * cancelled
6. Job notes are added during work
7. Invoice is generated
8. Payment status is recorded

---

## 6. Database Design Philosophy

* Use explicit foreign keys to enforce relationships
* Avoid hard deletes; use status flags instead
* Enforce business rules with PostgreSQL ENUM types
* Keep schema simple and extensible
* Treat the database as a source of truth

---

## 7. Main Database Entities

### Users

Stores admin and worker accounts.

### Customers

Represents individuals or businesses owning vehicles.

### Vehicles

Linked to customers; a customer may own multiple vehicles.

### Jobs

Represents repair or maintenance work done on a vehicle.

### Job Notes

Chronological logs of work, diagnostics, or observations.

### Invoices

Billing records linked one-to-one with jobs.

---

## 8. API Design Principles

* RESTful endpoints
* Clear separation between validation, logic, and persistence
* No business logic inside route handlers
* SQL queries isolated in a dedicated module
* Authentication and authorization enforced via dependencies

---

## 9. Project Structure

```
autorepair_erp/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI application and routes
│   │   ├── database.py    # PostgreSQL connection handling
│   │   ├── models.py      # Pydantic schemas
│   │   ├── queries.py     # Raw SQL queries
│   │   └── auth.py        # Authentication and authorization
│   ├── sql/
│   │   ├── init.sql       # Database schema
│   │   ├── seed.sql       # Initial data
│   │   └── migrations/    # Manual schema changes
│   ├── requirements.txt
│   └── .env
├── frontend/
└── docker-compose.yml
```

---

## 10. Non-Goals (For MVP)

* Customer self-service portal
* Online payments
* Inventory and parts management
* Advanced accounting features
* Mobile application

These may be added in later iterations.

---

## 11. Future Enhancements

* Parts and inventory tracking
* Payment records and history
* Customer notifications (SMS/email)
* Reporting and analytics
* Role expansion (manager, accountant)

---

## 12. Success Criteria

The project is considered successful if:

* Core workshop workflow works end-to-end
* Role-based access is enforced
* Data integrity is preserved
* API is stable and understandable
* Codebase remains readable and modular

---

## 13. Conclusion

This project focuses on learning backend system design through a realistic business domain. It prioritizes correctness, clarity, and maintainability over feature count or complexity, providing a strong foundation for future ERP-scale development.
