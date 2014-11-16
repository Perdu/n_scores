DROP DATABASE IF EXISTS n_scores2;
CREATE DATABASE n_scores2;
connect n_scores2;

-- CREATE TABLE `players` (
--        id int(10) NOT NULL AUTO_INCREMENT,
--        pseudo varchar(100) NOT NULL,
--        is_hacker int(1) DEFAULT 0,
--        is_cheater int(1) DEFAULT 0,
--        PRIMARY KEY (`id`)
-- );

-- id will be level name directly put into INT
-- e.g. "95-4" is 954
-- episodes will end in 5

-- CREATE TABLE `levels` (
--       id int(3) NOT NULL,
--       is_episode int(1),
--       PRIMARY KEY (`id`)
-- );

-- score stored into the "number of frames" form

CREATE TABLE `score` (
       level_id int(3) NOT NULL,
       pseudo varchar(100) NOT NULL,
--       player_id int(10) NOT NULL,
       `timestamp` timestamp,
       score int(10) unsigned NOT NULL,
       place int(1) NOT NULL,
       PRIMARY KEY (`level_id`, `pseudo`, `timestamp`)
--     CONSTRAINT `player_id_foreign` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`)
--     CONSTRAINT `level_id_foreign` FOREIGN KEY (`level_id`) REFERENCES `levels` (`id`)
);
