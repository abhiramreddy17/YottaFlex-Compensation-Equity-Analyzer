# YottaFlex Compensation Equity Analyzer

## 1. Project description

The **YottaFlex Compensation Equity Analyzer** is a Python-based demo
application that helps an HR or compensation team review employee
salaries against the salary range for their role, level, and work
location.

The application uses generated (synthetic) employee data. It
standardizes salaries into a common currency, adjusts them for
full-time-equivalent (FTE) status, compares them with the matching
compensation band, and highlights records that may need further review.

It includes: - A **Streamlit dashboard** to explore compensation
results. - A **Python analysis engine** for salary normalization and
compensation calculations. - A **FastAPI backend** that exposes analysis
information through API endpoints. - **Synthetic CSV datasets** for
employees, salary history, roles, locations, levels, compensation bands,
and related records. - **Validation and automated tests** to check data
quality and important business rules. - Separate **ground-truth
examples** for testing known scenarios.

> **Important:** This is a demonstration project using synthetic data. A
> flagged record is a signal for investigation, not proof of
> discrimination or unfair treatment. The application does not change
> payroll. Any compensation decision must be reviewed and approved by
> authorized people.

## 2. How the project works

The basic workflow is:

1.  Create synthetic employee and compensation data.
2.  Read each employee's latest salary record.
3.  Match the employee to the applicable role, level, location, and
    compensation band.
4.  Convert salary and band values into INR using the sample
    exchange-rate table.
5.  Normalize salary using the employee's recorded FTE.
6.  Calculate the **compa-ratio** (normalized salary divided by band
    midpoint).
7.  Identify records that may need review, including configured data or
    approval exceptions.
8.  Display the results in the dashboard and expose selected results
    through the API.

## 3. Project folder structure

After extracting the ZIP file, the project should look similar to this:

``` text
YottaFlex_Compensation_Analyzer/
│
├── app/                 # Python application and analysis logic
├── dashboard/           # Streamlit dashboard
├── data/                # Synthetic CSV input data
├── documentation/       # Business rules, schema and data dictionary
├── ground_truth/        # Separate labelled test scenarios
├── tests/               # Automated tests
├── requirements.txt     # Python packages required by the project
└── README.md             # This guide
```

Run all commands below from the main project folder:
`YottaFlex_Compensation_Analyzer`

## 4. Software requirements

Install these before starting:

-   Python 3.10 or later
-   Visual Studio Code (recommended)
-   Internet connection for installing Python packages

To check Python, open the VS Code terminal and run:

``` bash
python --version
```

If Windows does not recognize `python`, try:

``` bash
py --version
```

## 5. Step-by-step setup on Windows

### Step 1 --- Extract and open the project

1.  Download the project ZIP file.
2.  Right-click the ZIP file and select **Extract All**.
3.  Open Visual Studio Code.
4.  Select **File → Open Folder**.
5.  Choose the extracted `YottaFlex_Compensation_Analyzer` folder.
6.  In VS Code, select **Terminal → New Terminal**.

Make sure the terminal is at the project root. You should see
`requirements.txt` when you run:

``` powershell
dir
```

### Step 2 --- Create a virtual environment

A virtual environment keeps this project's Python packages separate from
other Python projects.

``` powershell
python -m venv .venv
```

### Step 3 --- Activate the virtual environment

**Option A: PowerShell**

``` powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell says that script execution is disabled, use the following
command for your current Windows user:

``` powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Confirm with `Y` if PowerShell asks. Then activate again:

``` powershell
.\.venv\Scripts\Activate.ps1
```

**Option B: Command Prompt (without changing PowerShell settings)**

In VS Code, open the terminal profile dropdown, choose **Command
Prompt**, and run:

``` cmd
.venv\Scripts\activate.bat
```

When activation succeeds, `(.venv)` appears at the beginning of the
terminal prompt.

### Step 4 --- Install the required packages

With the virtual environment activated, run:

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Wait for the installation to finish.

## 6. Run the Streamlit dashboard

The dashboard is the easiest way to explore the project.

1.  Open a VS Code terminal at the project root.
2.  Activate `.venv` if it is not already active.
3.  Run:

``` bash
streamlit run dashboard/dashboard.py
```

Streamlit will print a local address in the terminal. Open the address
in your browser. It is usually:

**http://localhost:8501**

Keep the terminal running while you use the dashboard. To stop the
dashboard, click inside that terminal and press **Ctrl + C**.

## 7. Run the FastAPI backend (optional)

The API can run separately from the dashboard.

1.  Open a **second** VS Code terminal.
2.  Move to the project root if necessary.
3.  Activate the same virtual environment.
4.  Run:

``` bash
uvicorn app.main:app --reload
```

Open the interactive API documentation:

**http://127.0.0.1:8000/docs**

The project includes these endpoints:

-   `GET /health` --- checks whether the API is running.
-   `GET /summary` --- returns a summary of the analysis.
-   `GET /anomalies` --- returns flagged records.
-   `GET /review-proposals` --- returns review proposals.
-   `GET /employees/{employee_id}` --- retrieves an employee's
    information.
-   `POST /load-sqlite` --- loads the CSV tables into the local SQLite
    database.

To stop the API, click its terminal and press **Ctrl + C**.

## 8. Generate the synthetic dataset (optional)

The ZIP already contains generated sample data, so you can run the
dashboard without generating it again.

To regenerate the full dataset with 5,000 employees and a fixed random
seed, run this from the project root:

``` bash
python -m app.data_generator --employees 5000 --seed 20261022
```

For a smaller dataset while developing:

``` bash
python -m app.data_generator --employees 100 --seed 20261022
```

The generator writes CSV files under `data/` and labelled examples under
`ground_truth/`. The ground-truth file is kept separate from the
analysis input so it can be used to validate the detection logic rather
than act as an input to it.

**Note:** Generating data again may replace the existing generated files
in those folders. Keep a backup if you have made your own changes.

## 9. Run the automated tests

From the project root, with the virtual environment activated, run:

``` bash
pytest -q
```

The test suite checks key parts of data generation, compensation
calculations, and anomaly detection. The supplied project version was
tested with **6 passing tests**.

## 10. Main calculations in simple terms

-   **Currency normalization:** Converts salary and compensation-band
    values into INR using the project's illustrative exchange rates.

-   **FTE normalization:** Adjusts recorded salary to a full-time
    equivalent basis using the FTE value stored with the salary record.

-   **Compa-ratio:** Compares normalized salary with the midpoint of the
    applicable compensation band.

    `Compa-ratio = Normalized salary ÷ Compensation band midpoint`

    Example: if normalized salary is ₹900,000 and the band midpoint is
    ₹1,000,000, the compa-ratio is `0.90` or `90%`.

-   **Anomaly flag:** Identifies a condition that may require
    investigation. It is not, by itself, a conclusion about why an
    employee is paid differently.

The sample exchange rates and compensation bands are illustrative, not
official market or company data. See the files in `documentation/` for
the detailed rules, schema, and field definitions.

## 11. Troubleshooting

  ------------------------------------------------------------------------------------------------
  Problem                             What to do
  ----------------------------------- ------------------------------------------------------------
  `python` is not recognized          Install Python and enable **Add Python to PATH**, or try
                                      `py` instead of `python`.

  PowerShell says running scripts is  Use the Command Prompt activation command in Step 3, or
  disabled                            follow the PowerShell instructions there.

  `streamlit` is not recognized       Activate `.venv`, then run
                                      `pip install -r requirements.txt`.

  `No module named ...`               Check that `.venv` is active and install packages again with
                                      `pip install -r requirements.txt`.

  Port 8501 is already in use         Stop the other Streamlit process, or run
                                      `streamlit run dashboard/dashboard.py --server.port 8502`.

  


