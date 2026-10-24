# SmartOps Management System

### Inventory Management, Business Intelligence & Predictive Analytics

SmartOps is a full-stack inventory management and analytics platform designed for small retail and beverage businesses.

The project integrates inventory tracking, transaction history, demand forecasting, and business intelligence into a centralized web application.

## Tech Stack

| Category | Technologies |
|----------|--------------|
| Backend | Python, Flask, SQLAlchemy |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Data Analytics | Pandas, NumPy |
| Machine Learning | Scikit-learn, Random Forest |
| Testing | Pytest, Flask Test Client |
| Deployment | Gunicorn, GitHub |

## Key Features

### 1. Inventory Management
- Create and update inventory items.
- Track stock quantities, categories, and unit costs.
- Monitor inventory value and reorder thresholds.

### 2. Inventory Transactions
- Record stock receipts, consumption, waste, and adjustments.
- Maintain transaction history and stock balance changes.
- Track business dates separately from transaction timestamps.
- Aggregate daily inventory consumption.

### 3. Business Intelligence
- Inventory analytics dashboard.
- Inventory value and category breakdown.
- Stock status monitoring.
- Data-driven inventory insights.

### 4. Demand Forecasting
- 7-day moving-average forecasting.
- 30, 60, and 90-day demand projections.
- Inventory coverage estimates.
- Insufficient-data validation.

### 5. Smart Reorder Recommendations
- Calculate reorder points.
- Estimate days until reorder.
- Incorporate supplier lead time and safety stock.
- Recommend replenishment quantities.

### 6. Machine Learning Evaluation
- Random Forest regression.
- Moving-average baseline comparison.
- MAE and RMSE evaluation metrics.
- Feature importance analysis.
- Interactive model evaluation dashboard.

## Machine Learning Transparency

The current ML evaluation uses synthetic inventory consumption data for demonstration and testing.

Reported model performance represents results on simulated data, not verified operational improvements at a real business.

Production forecasting with real inventory history is a future development goal.

## Installation

### Requirements
- Python 3.11
- MySQL
- Git

### Clone Repository

    git clone https://github.com/ngson927/Smartops-Management-System.git
    cd Smartops-Management-System

### Create Virtual Environment

    python3 -m venv .venv
    source .venv/bin/activate

### Install Dependencies

    pip install -r requirements.txt

### Configure Environment

    cp .env.example .env

Update the local database credentials and generate a strong SECRET_KEY in the `.env` file.

Create the MySQL database and configure an account with appropriate permissions.

### Apply Database Migrations

    python -m flask --app run:app db upgrade

### Run Application

    python run.py

Application:

http://127.0.0.1:5050

A valid user account is required to access protected pages. Public self-registration is disabled.

## Testing

Run automated tests:

    python -m pytest -v

Latest local validation:
- 36 automated tests passed.
- Daily usage integration check passed for DEMO and REAL sources.
- Integration check validates database reads and API aggregation.

The integration check is read-only and does not replace database-isolated transaction write tests.

## Project Status

SmartOps is an active portfolio and development project.

Implemented:
- Inventory management
- Transaction recording
- Daily consumption aggregation
- Business intelligence dashboards
- Moving-average forecasting
- Smart reorder recommendations
- Synthetic ML model evaluation

Planned:
- Real operational data integration
- Expanded integration testing
- Production ML forecasting
- Cloud deployment and monitoring

## Data & Security

- Synthetic data is used for ML demonstration.
- Local environment credentials are excluded from Git.
- Protected application routes require authentication.
- The current application is not yet certified as production-ready.

## Author

Son Nguyen

Computer Science | Software Engineering | Data Analytics

GitHub: https://github.com/ngson927
