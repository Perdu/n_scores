DROP DATABASE IF EXISTS n_scores2;
CREATE DATABASE n_scores2;
connect n_scores2;

-- contains a copy of all score at every timestamp (download)
CREATE TABLE `score` (
       level_id int(3) NOT NULL,
       pseudo varchar(100) NOT NULL,
       `timestamp` timestamp DEFAULT CURRENT_TIMESTAMP,
       score int(10) unsigned NOT NULL,
       place int(1) NOT NULL,
       PRIMARY KEY (`level_id`, `pseudo`, `timestamp`)
);

-- contains scores only once
CREATE TABLE `score_unique` (
       level_id int(3) NOT NULL,
       pseudo varchar(100) NOT NULL,
       `timestamp` timestamp DEFAULT CURRENT_TIMESTAMP,
       score int(10) unsigned NOT NULL,
       place int(1) NOT NULL,
       demo TEXT,
       PRIMARY KEY (`level_id`, `pseudo`, `score`)
);
