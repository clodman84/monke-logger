CREATE TABLE IF NOT EXISTS themes(
    theme TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS themes_records_bridge(
    theme TEXT,
    record_name TEXT,
    CONSTRAINT themes_records_pk PRIMARY KEY (theme, record_name),
    CONSTRAINT theme_fk FOREIGN KEY (theme) REFERENCES themes (theme)
);

CREATE TABLE IF NOT EXISTS themes_benchmarks_bridge(
    theme TEXT,
    benchmark_name TEXT,
    CONSTRAINT benchmark_name_pk PRIMARY KEY (theme, benchmark_name),
    CONSTRAINT benchmark_fk FOREIGN KEY (theme) REFERENCES themes (theme)
);

CREATE TABLE IF NOT EXISTS records(
    timestamp TIMESTAMP,
    theme TEXT,
    record_name TEXT,
    value INTEGER,
    CONSTRAINT record_name_fk FOREIGN KEY (theme, record_name) REFERENCES themes_records_bridge (theme, record_name)
);

CREATE TABLE IF NOT EXISTS benchmarks(
    timestamp TIMESTAMP,
    theme TEXT,
    benchmark_name TEXT,
    value INTEGER,
    CONSTRAINT benchmark_name_fk FOREIGN KEY (theme, benchmark_name) REFERENCES themes_benchmarks_bridge (theme, benchmark_name)
);
