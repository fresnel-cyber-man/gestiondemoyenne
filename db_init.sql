-- db_init.sql -- Création des tables (version simple & professionnelle)
CREATE TABLE IF NOT EXISTS classes (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS eleves (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    matricule VARCHAR(50) NOT NULL UNIQUE,
    classe_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS matieres (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    coefficient INT NOT NULL CHECK (coefficient >= 1),
    classe_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    UNIQUE (nom, classe_id)
);

CREATE TABLE IF NOT EXISTS notes (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    eleve_id INT NOT NULL REFERENCES eleves(id) ON DELETE CASCADE,
    matiere_id INT NOT NULL REFERENCES matieres(id) ON DELETE CASCADE,
    note NUMERIC(4,2) NOT NULL CHECK (note >= 0 AND note <= 20),
    UNIQUE (eleve_id, matiere_id)
);

-- Données de test
TRUNCATE TABLE notes, eleves, matieres, classes RESTART IDENTITY CASCADE;

INSERT INTO classes (nom) VALUES ('6A'), ('5B'), ('Terminale S');

INSERT INTO eleves (nom, prenom, matricule, classe_id) VALUES
('Dossou','Marc','ETU001',1),
('Adjovi','Sandra','ETU002',1),
('Gnon','Elias','ETU003',2),
('Kouassi','Aline','ETU004',3);

INSERT INTO matieres (nom, coefficient, classe_id) VALUES
('Mathématiques',4,1),
('Physique',3,1),
('Informatique',5,1),
('Anglais',1,1),
('Mathématiques',4,2),
('Physique',3,2),
('Informatique',5,3);

-- Notes (liées aux élèves/matières ci-dessus)
INSERT INTO notes (eleve_id, matiere_id, note) VALUES
(1,1,14.50),(1,2,12.00),(1,3,17.00),(1,4,13.00),
(2,1,16.00),(2,2,14.50),(2,3,18.00),(2,4,17.50),
(3,5,10.00),(3,6,11.50),
(4,7,19.00);
