CREATE TABLE IF NOT EXISTS themes(
    id INTEGER PRIMARY KEY,
    created_on TIMESTAMP,
    name TEXT
);

CREATE TABLE IF NOT EXISTS types(
    id INTEGER PRIMARY KEY,
    created_on TIMESTAMP,
    theme_id INTEGER,
    name TEXT,
    unit TEXT,
    display_type TEXT, --Record/Benchmark
    representation TEXT, --Time/T_Interval/Percentages/Accurate Time/Custom, etc
    CONSTRAINT theme_type_fk FOREIGN KEY (theme_id) REFERENCES themes (id) ON DELETE CASCADE,
    UNIQUE(name, theme_id)
);

CREATE TABLE IF NOT EXISTS data(
    type_id INTEGER,
    created_on TIMESTAMP,
    timestamp TIMESTAMP,
    val INTEGER,
    CONSTRAINT data_type_fk FOREIGN KEY (type_id) REFERENCES types (id) ON DELETE CASCADE
);
