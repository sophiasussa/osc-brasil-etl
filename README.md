# OSC Brasil — ETL

ETL pipeline responsible for extracting, transforming, and loading public data from the [Mapa das OSCs](https://mapaosc.ipea.gov.br/) into a structured format for the **OSC Brasil** application.

The pipeline prepares the dataset that will be consumed by the OSC Brasil backend and made available through its API to the mobile application.

## Architecture

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

## Responsibilities

The ETL pipeline is responsible for:

* Extracting data from the Mapa das OSCs dataset.
* Cleaning and standardizing raw data.
* Converting values to appropriate data types.
* Handling missing and invalid values.
* Validating geographic coordinates and other data constraints.
* Loading processed data into PostgreSQL.
* Supporting reproducible data updates.

## Project Structure

```text
osc-brasil-etl/
│
├── etl/
│   ├── __init__.py
│   ├── extract.py       # Data extraction
│   ├── transform.py     # Cleaning and transformation
│   └── load.py          # Data loading
│
├── tests/               # Automated tests
│
├── data/                # Local datasets (not committed)
│   └── .gitkeep
│
├── docs/                # Dataset and pipeline documentation
│
├── main.py              # Pipeline entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .gitignore
└── README.md
```

## Technologies

* Python 3.12+
* Pandas
* SQLAlchemy
* PostgreSQL
* Pytest
* python-dotenv
* Docker

## Data Source

The pipeline uses public data provided by the **Mapa das Organizações da Sociedade Civil (Mapa das OSCs)**, maintained by IPEA.

Source:

https://mapaosc.ipea.gov.br/

The dataset is used as the primary source for organization information in the OSC Brasil application.

## Getting Started

### Requirements

Before running the project, make sure you have:

* Python 3.12+
* PostgreSQL
* Git
* Docker (optional)

### Installation

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

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
DB_URL=postgresql://user:password@localhost:5432/osc_brasil
```

Do not commit `.env` or credentials to the repository.

### Dataset

Place the source dataset in:

```text
data/oscs.csv
```

The complete dataset is not committed to the repository.

For development and testing, a smaller sample dataset can be used.

## Running the Pipeline

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

## Testing

Run the test suite with:

```bash
pytest
```

Tests are organized under:

```text
tests/
```

The test suite covers the extraction, transformation, and loading components of the pipeline.

## Data Updates

The ETL pipeline is designed to update the PostgreSQL database whenever a new version of the source dataset becomes available.

The ETL process is independent from the OSC Brasil backend.

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

## Development Roadmap

### Step 1 — Dataset Investigation

* [ ] Analyze the source dataset
* [ ] Document available fields
* [ ] Identify identifiers and relationships
* [ ] Identify missing and optional fields
* [ ] Map dataset fields to the OSC Brasil API requirements

### Step 2 — Data Model

* [ ] Define the PostgreSQL schema
* [ ] Define relationships
* [ ] Define primary and foreign keys
* [ ] Define indexes required by the API
* [ ] Define data validation rules

### Step 3 — ETL

* [ ] Improve extraction
* [ ] Refine transformations
* [ ] Implement PostgreSQL loading
* [ ] Handle dataset updates
* [ ] Add data validation
* [ ] Add automated tests

### Step 4 — Integration

* [ ] Populate the OSC Brasil PostgreSQL database
* [ ] Validate the data through the backend API
* [ ] Support the `/organizations` endpoint
* [ ] Support the `/organizations/{id}` endpoint

## Related Projects

The OSC Brasil project is divided into three repositories:

* **osc-brasil-etl** — data extraction, transformation, and loading.
* **osc-brasil-backend** — FastAPI backend and REST API.
* **osc-brasil-frontend** — Flutter mobile application.

## License

This project is licensed under the MIT License.
