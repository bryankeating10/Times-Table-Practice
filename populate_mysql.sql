-- MySQL 8+ population (run in mysql client)
WITH RECURSIVE nums AS (SELECT 1 AS n UNION ALL SELECT n+1 FROM nums WHERE n < 30)
INSERT IGNORE INTO multiplication_table (multiplicand, multiplier, product)
SELECT a.n, b.n, a.n*b.n FROM nums a CROSS JOIN nums b;
