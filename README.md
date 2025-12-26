## Job Market Pulse
Job Market Pulse is an automated data pipeline that monitors the remote job market by periodically scraping RemoteOK job listings.  
The system preserves historical data across runs, detects newly appearing roles, and provides time-based insights into skills, job families, and market trends through an interactive dashboard.

## Purpose
Job listings change continuously, but most platforms expose only the current state of the market.
This project was built to capture and analyze how remote job demand evolves over time, with a focus on skill trends, job turnover, and data freshness.

## System Architecture
The project consists of three main components:
1. **Automated Scraping Pipeline**
   - Selenium-based scraper collects job postings from RemoteOK
   - Runs on a fixed schedule using GitHub Actions
   - Each run is logged with metadata (timestamps, job counts, status)
2. **Data Processing & Analytics**
   - Raw job data is stored append-only for historical preservation
   - Jobs are deduplicated and clustered into high-level job families
   - Run-level metrics track new vs existing jobs over time
3. **Interactive Dashboard**
   - Streamlit frontend reads processed data
   - Displays skill distributions, job family composition, and trends

## Data Pipeline
The pipeline produces and maintains four core datasets:
- `data/raw/remote_jobs.csv`  
  Append-only raw job postings across all scrape runs.
- `data/meta/scrape_runs.csv`  
  Metadata for each pipeline execution (run ID, timestamps, job count, status).
- `data/processed/data_clean.csv`  
  Latest deduplicated snapshot of active jobs with derived features.
- `data/processed/run_job_info.csv`  
  Run-level analytics including new vs existing job counts.

## Automation
Using GitHub Actions:
- Scraping and processing run on a scheduled cron job
- No manual intervention is required
- Each run commits updated data back to the repository
- The dashboard reflects the latest successful pipeline run

## Dashboard Features
The Streamlit application provides:
- Job search and filtering by skill, role, or company
- Skill composition (“Skill DNA”) by job family
- Comparison of skill importance across job families
- Market trends showing total jobs vs newly appearing jobs
- Data freshness indicators based on pipeline run metadata

