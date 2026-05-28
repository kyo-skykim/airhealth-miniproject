# Image bundling the AirHealth pipeline (ingestion, dbt, DS, dashboard).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /opt/airflow/project

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["bash", "-lc", "make run-local && streamlit run dashboard/app.py --server.address=0.0.0.0"]
