# 💼 Freelancer Management Software

> 🐍 **Software Engineering Exam Project**
> **Author: Sacco Emanuele**

A comprehensive, local-first desktop application built in Python for freelance professionals. It manages the entire business workflow: from clients, projects, and inventory to PDF invoicing and tax estimations, all from a single, secure interface.



---

## 🌟 Key Features

* **Main Dashboard:** An at-a-glance overview of active projects, unpaid invoices, upcoming deadlines, and year-to-date (YTD) financial statistics (Income vs. Expenses).
* **Address Book:** Full CRUD (Create, Read, Update, Delete) for clients and suppliers. Includes import/export from CSV and Excel files.
* **Project Management:**
    * Create projects and link them to clients.
    * Define project phases and set deadlines.
    * Integrated **Time Tracking** for billable and non-billable hours.
    * Store and manage project-related files (PDFs, DWGs, etc.).
* **Invoicing & PDF (Documents):**
    * Create professional Quotes (Preventivi) and Invoices (Fatture).
    * Automatic sequential numbering (e.g., `F-2025/001`).
    * Calculates VAT, Discounts, and **Withholding Tax** (Ritenuta d'Acconto).
    * One-click conversion of a Quote into an Invoice.
    * Export to **professional PDF** files using an HTML/CSS template.
* **Inventory:**
    * Manage an item catalog for materials and components.
    * Track purchase price and stock levels.
    * Stock is **automatically deducted** when an item is added to an invoice.
* **Accounting (Ledger):**
    * A full financial **Ledger** (Registro Movimenti) for all income and expenses.
    * Automatically links payments to invoices, updating their status to "Paid".
    * Annual export for your accountant (CSV/Excel).
* **Tax Estimation:**
    * A dashboard to estimate quarterly VAT payments (Debit vs. Credit).
    * YTD projection for INPS and IRPEF contributions based on configurable rates.

---

## 🛠 Tech Stack & Architecture

The project is built on a clean separation of concerns between business logic (Backend) and the user interface (Frontend).

| Component | Technology | Description |
| :--- | :--- | :--- |
| **GUI** | `CustomTkinter` | For a modern, themed desktop interface. |
| **Data Storage** | `pickle` | For local-first, offline, and secure data persistence. |
| **Data Analysis** | `Pandas` | For data aggregation and Excel/CSV exports. |
| **PDF Generation** | `WeasyPrint` & `Jinja2` | For rendering professional HTML/CSS templates into PDFs. |
| **Charting** | `Matplotlib` | For generating cash flow and productivity charts. |

---

## 📁 Project Structure

The modular structure ensures high maintainability and scalability.

```
ProgettoSoftwareGestionale/
│
├── backend/
│   │
│   ├── __init__.py                # (Tells Python this is a package)
│   ├── persistence.py             # (Handles all read/write ops for .pkl data files and settings)
│   ├── email_utils.py             # (Utility for connecting to SMTP and sending emails)
│   │
│   ├── address_book.py            # (Business logic for Clients/Suppliers CRUD & Import/Export)
│   ├── projects.py                # (Business logic for Projects, Phases, Time Tracking, and File Copying)
│   ├── inventory.py               # (Business logic for Warehouse item CRUD and Stock management)
│   ├── documents.py               # (Business logic for Quotes, Invoices, PDF generation, and Stock reduction)
│   ├── calendar.py                # (Business logic for manual events and automatic deadline generation)
│   ├── ledger.py                  # (Business logic for the financial ledger, income/expenses, and accountant exports)
│   ├── tax.py                     # (Business logic for calculating estimated VAT, INPS, and IRPEF)
│   ├── time_reports.py            # (Business logic for analyzing time tracking data and generating charts)
│   └── dashboard.py               # (Business logic for aggregating all data for the main dashboard view)
│
├── frontend/
│   │
│   ├── __init__.py                # (Tells Python this is a package)
│   ├── page_base.py               # (A base class that all other GUI pages inherit from)
│   │
│   ├── dashboard.py               # (GUI Page: The main dashboard screen)
│   ├── address_book.py            # (GUI Page: The Address Book list/detail view)
│   ├── projects.py                # (GUI Page: The Projects list/detail view with tabs)
│   ├── inventory.py               # (GUI Page: The Warehouse/Inventory list/detail view)
│   ├── documents.py               # (GUI Page: The Quotes and Invoices tabs)
│   ├── calendar.py                # (GUI Page: The Calendar view and SMTP settings)
│   ├── ledger.py                  # (GUI Page: The Financial Ledger and Tax Estimation tabs)
│   └── time_reports.py            # (GUI Page: The Time Tracking reports and charts)
│
├── frontend_gui.py              # (MAIN ENTRY POINT. Run this file to start the application)
├── invoice_template.html    # (HTML/CSS template used by WeasyPrint to generate PDFs)
└── requirements.txt         # (List of all Python dependencies for 'pip install -r')
```

---

## ⚡ Setup & Execution

Follow these steps to get the application running.

### 1. Prerequisites
- Python 3.10+
- (Recommended) A virtual environment (`venv`)

### 2. Install Python Dependencies
Install all required Python libraries.
```
pip install -r requirements.txt
```
### 3. 🚨 Install GTK3 (Critical for PDFs)
The PDF library (`WeasyPrint`) requires a non-Python dependency called **GTK3**.

**Add GTK3 to your system's PATH**

## 🏁 Conclusion & Key Takeaways

✅ **Modular Architecture (View-Logic)** → The clean separation between `frontend/` and `backend/` makes the code maintainable and allows the UI to be swapped (e.g., for a web app) without changing the business logic.

✅ **Full Financial Lifecycle** → The software handles the entire freelance workflow: from Quote, to Invoice, to Inventory management, to logging the Payment in the Ledger, and finally to Tax Estimation.

✅ **Time-Saving Automation** → Features like Quote-to-Invoice conversion, automatic stock deduction, and auto-generated calendar deadlines automate manual, error-prone tasks.

✅ **Local-First and Secure** → All sensitive data (clients, invoices, accounts) resides exclusively on the user's local machine. There is no cloud dependency or subscription.

✅ **Professional Reporting** → Generates professional-grade PDFs for clients and comprehensive Excel/PDF reports for accounting and internal analysis.
