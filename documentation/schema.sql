-- Portable relational schema reference. CSV -> SQLite loading is implemented in app/database.py.
CREATE TABLE Role (role_id VARCHAR(20) PRIMARY KEY, role_name VARCHAR(100) UNIQUE NOT NULL);
CREATE TABLE Level (level_id VARCHAR(20) PRIMARY KEY, level_name VARCHAR(20) UNIQUE NOT NULL, level_order INTEGER NOT NULL);
CREATE TABLE Location (location_id VARCHAR(20) PRIMARY KEY, city VARCHAR(100) UNIQUE NOT NULL, currency VARCHAR(3) NOT NULL);
CREATE TABLE Employee (
  employee_id VARCHAR(20) PRIMARY KEY, employee_name VARCHAR(100) NOT NULL,
  role_id VARCHAR(20) NOT NULL REFERENCES Role(role_id),
  level_id VARCHAR(20) NOT NULL REFERENCES Level(level_id),
  location_id VARCHAR(20) NOT NULL REFERENCES Location(location_id),
  joining_date DATE NOT NULL, employment_status VARCHAR(20) NOT NULL, fte REAL NOT NULL CHECK(fte > 0 AND fte <= 1)
);
CREATE TABLE CompensationBand (
  band_id VARCHAR(200) PRIMARY KEY, role_id VARCHAR(20) NOT NULL REFERENCES Role(role_id),
  level_id VARCHAR(20) NOT NULL REFERENCES Level(level_id),
  location_id VARCHAR(20) NOT NULL REFERENCES Location(location_id),
  currency VARCHAR(3) NOT NULL, min_salary REAL NOT NULL, mid_salary REAL NOT NULL,
  max_salary REAL NOT NULL, effective_start DATE NOT NULL, effective_end DATE NOT NULL,
  CHECK(min_salary <= mid_salary AND mid_salary <= max_salary)
);
CREATE TABLE SalaryRecord (
  salary_id VARCHAR(100) PRIMARY KEY, employee_id VARCHAR(20) NOT NULL REFERENCES Employee(employee_id),
  band_id VARCHAR(200) NOT NULL REFERENCES CompensationBand(band_id),
  effective_date DATE NOT NULL, end_date DATE NOT NULL, base_salary REAL NOT NULL,
  currency VARCHAR(3) NOT NULL, fte_at_record REAL NOT NULL, annualized BOOLEAN NOT NULL
);
