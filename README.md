# **OSC Brasil — ETL**

ETL pipeline responsible for extracting, transforming, and loading public data from the [Mapa das OSCs](https://mapaosc.ipea.gov.br/) into a structured format for the **OSC Brasil** application.

The pipeline prepares the dataset that will be consumed by the OSC Brasil backend and made available through its API to the mobile application.

## **Architecture**

The data flow is:

```text
Mapa das OSCs / IPEA
        │
        ▼
     Extract
        │
        ▼
    Transform
        │
        ▼
      Load
        │
        ▼
   PostgreSQL
        │
        ▼
 OSC Brasil Backend
        │
        ▼
 OSC Brasil Mobile
```

This repository is responsible only for the **data pipeline**. The backend API and mobile application are maintained in separate repositories.

## **Responsibilities**

The ETL pipeline is responsible for:

* Extracting data from the Mapa das OSCs dataset.
* Cleaning and standardizing raw data.
* Converting values to appropriate data types.
* Handling missing and invalid values.
* Validating geographic coordinates and other data constraints.
* Loading processed data into PostgreSQL.
* Providing automated tests for the ETL pipeline.

## **Project Structure**

```text
osc-brasil-etl/

├── etl/
│   ├── __init__.py
│   ├── extract.py       # Data extraction
│   ├── transform.py     # Cleaning and transformation
│   ├── load.py          # Data loading
│   └── models.py        # SQLAlchemy database models
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── data/
│   └── .gitkeep         # Local datasets (not committed)
│
├── main.py              # Pipeline entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .gitignore
├── docker-compose.yml   # PostgreSQL container
├── pytest.ini
└── README.md
```

## **Technologies**

* Python 3.12+
* Pandas
* SQLAlchemy
* PostgreSQL
* Pytest
* python-dotenv
* Docker

## **Data Source**

The pipeline uses public data provided by the **Mapa das Organizações da Sociedade Civil (Mapa das OSCs)**, maintained by IPEA.

Source:

[Mapa das OSCs](https://mapaosc.ipea.gov.br/)

The dataset is used as the primary source for organization information in the OSC Brasil application.

## **Getting Started**

### **Requirements**

Before running the project, make sure you have:

* Python 3.12+
* Git
* Docker

PostgreSQL is provided through Docker Compose.

### **Installation**

Clone the repository:

```bash
git clone <repository-url>
cd osc-brasil-etl
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### **Environment Variables**

Create a `.env` file based on `.env.example`:

```env
POSTGRES_DB=osc_brasil
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_URL=postgresql+psycopg://postgres:postgres@localhost:5432/osc_brasil
```

Do not commit `.env` or credentials to the repository.

### **Database**

Start PostgreSQL using Docker Compose:

```bash
docker compose up -d
```

To stop the database:

```bash
docker compose down
```

## **Dataset**

Place the source dataset in:

```text
data/osc.csv
```

The complete dataset is not committed to the repository because of its size.

For development and testing, a smaller sample dataset can be used.

## **Running the Pipeline**

Run the pipeline with:

```bash
python main.py
```

The pipeline performs the following steps:

```text
Extract
  ↓
Read source dataset
  ↓
Transform
  ↓
Clean and standardize data
  ↓
Load
  ↓
PostgreSQL
```

## **Testing**

Run the complete test suite with:

```bash
pytest
```

Tests are organized under:

```text
tests/
├── unit/
│   ├── test_extract.py
│   ├── test_transform.py
│   └── test_load.py
└── integration/
    └── test_pipeline.py
```

The test suite covers extraction, transformation, database loading, and integration with PostgreSQL.

Current status:

```text
29 tests passed
```

## **Data Updates**

The ETL process is independent from the OSC Brasil backend.

When a new version of the source dataset becomes available, the ETL can be executed to process and load the data into PostgreSQL.

Users of the mobile application do **not** execute the ETL pipeline. The application reads the processed data already stored in PostgreSQL through the backend API.

```text
Dataset Update
      ↓
ETL Pipeline
      ↓
PostgreSQL
      ↓
FastAPI Backend
      ↓
Flutter Application
```

The strategy for updating existing records and processing the complete dataset is still being evaluated.

## **Development Roadmap**

### **Step 1 — Dataset Investigation**

* [x] Analyze the source dataset
* [x] Identify identifiers and relationships
* [x] Identify missing and optional fields
* [x] Map relevant dataset fields to the application requirements

### **Step 2 — Data Model**

* [x] Define the initial PostgreSQL schema
* [x] Define relationships
* [x] Define primary and foreign keys
* [x] Define initial data validation constraints
* [ ] Review the database model

### **Step 3 — ETL**

* [x] Implement extraction
* [x] Implement transformations
* [x] Implement PostgreSQL loading
* [x] Add unit tests
* [x] Add integration tests
* [ ] Evaluate loading performance with the complete dataset
* [ ] Define the final dataset update strategy

### **Step 4 — Integration**

* [ ] Populate the complete OSC Brasil PostgreSQL database
* [ ] Validate the data through the backend API
* [ ] Support the `/organizations` endpoint
* [ ] Support the `/organizations/{id}` endpoint

## **Related Projects**

The OSC Brasil project is divided into three repositories:

* **osc-brasil-etl** — data extraction, transformation, and loading.
* **osc-brasil-backend** — FastAPI backend and REST API.
* **osc-brasil-frontend** — Flutter mobile application.

## **License**

This project is licensed under the MIT License.
