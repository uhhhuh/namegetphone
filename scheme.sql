CREATE TABLE person (
       	id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL
);

CREATE TABLE phones (
        id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        person_id   INTEGER NOT NULL REFERENCES person(id),
        phone       TEXT
);

CREATE TABLE birthdays (
        id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        person_id   INTEGER NOT NULL REFERENCES person(id),
        birthday    TEXT
);

CREATE TABLE addresses (
        id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        person_id   INTEGER NOT NULL REFERENCES person(id),
        address     TEXT NOT NULL
);

CREATE TABLE persons_associated (
        id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        person_id   INTEGER NOT NULL REFERENCES person(id),
        name        TEXT NOT NULL,
        birth       TEXT
);
