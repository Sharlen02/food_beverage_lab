--Étape 1 – Préparation de l’environnement Snowflake
create database if not exists ANYCOMPANY_LAB;

use database ANYCOMPANY_LAB;

create schema if not exists BRONZE;
create schema if not exists SILVER;

use database ANYCOMPANY_LAB;
use schema BRONZE;
create or replace stage food_beverage_stage
    URL = 's3://logbrain-datalake/datasets/food-beverage/';

LIST @anycompany_lab.bronze.food_beverage_stage;

--Étape 2 – Création des tables

--Fichier .csv
CREATE OR REPLACE FILE FORMAT CSV_FORMAT
  type = 'CSV'
  field_delimiter = ','
  record_delimiter = '\n'
  skip_header = 1
  field_optionally_enclosed_by = '"'
  null_if = (''); 

CREATE OR REPLACE TABLE customer_demographics (
    customer_id STRING,
    name STRING,
    date_of_birth DATE,
    gender STRING,
    region STRING,
    country STRING,
    city STRING,
    marital_status STRING,
    annual_income NUMBER(10,2)
);

CREATE OR REPLACE TABLE customer_service_interactions (
    interaction_id STRING,
    interaction_date DATE,
    interaction_type STRING,
    issue_category STRING,
    description STRING,
    duration_minutes NUMBER,
    resolution_status STRING,
    follow_up_required STRING,
    customer_satisfaction NUMBER
);

CREATE OR REPLACE TABLE financial_transactions (
    transaction_id STRING,
    transaction_date DATE,
    transaction_type STRING,
    amount NUMBER(12,2),
    payment_method STRING,
    entity STRING,
    region STRING,
    account_code STRING
);

CREATE OR REPLACE TABLE promotions_data (
    promotion_id STRING,
    product_category STRING,
    promotion_type STRING,
    discount_percentage FLOAT,
    start_date DATE,
    end_date DATE,
    region STRING
);

CREATE OR REPLACE TABLE marketing_campaigns (
    campaign_id STRING,
    campaign_name STRING,
    campaign_type STRING,
    product_category STRING,
    target_audience STRING,
    start_date DATE,
    end_date DATE,
    region STRING,
    budget NUMBER(12,2),
    reach NUMBER,
    conversion_rate FLOAT
);

CREATE OR REPLACE TABLE product_reviews (
    review_id NUMBER,
    product_id STRING,
    reviewer_id STRING,
    reviewer_name STRING,
    rating NUMBER,
    review_date TIMESTAMP,
    review_title STRING,
    review_text STRING,
    product_category STRING
);

CREATE OR REPLACE TABLE logistics_and_shipping (
    shipment_id STRING,
    order_id STRING,
    ship_date DATE,
    estimated_delivery DATE,
    shipping_method STRING,
    status STRING,
    shipping_cost NUMBER(10,2),
    destination_region STRING,
    destination_country STRING,
    carrier STRING
);

CREATE OR REPLACE TABLE supplier_information (
    supplier_id STRING,
    supplier_name STRING,
    product_category STRING,
    region STRING,
    country STRING,
    city STRING,
    lead_time NUMBER,
    reliability_score FLOAT,
    quality_rating STRING
);

CREATE OR REPLACE TABLE employee_records (
    employee_id STRING,
    name STRING,
    date_of_birth DATE,
    hire_date DATE,
    department STRING,
    job_title STRING,
    salary NUMBER(12,2),
    region STRING,
    country STRING,
    email STRING
);


--Étape 3 – Chargement des données (fichier .csv)
COPY INTO customer_demographics
FROM @anycompany_lab.bronze.food_beverage_stage/customer_demographics.csv
FILE_FORMAT = csv_format;

select * from customer_demographics limit 10;
select count(*) from customer_demographics; -- 5 000 Lignes

COPY INTO customer_service_interactions
FROM @anycompany_lab.bronze.food_beverage_stage/customer_service_interactions.csv
FILE_FORMAT = csv_format;

COPY INTO financial_transactions
FROM @anycompany_lab.bronze.food_beverage_stage/financial_transactions.csv
FILE_FORMAT = csv_format;

COPY INTO promotions_data
FROM @anycompany_lab.bronze.food_beverage_stage/promotions-data.csv
FILE_FORMAT = csv_format;

COPY INTO marketing_campaigns
FROM @anycompany_lab.bronze.food_beverage_stage/marketing_campaigns.csv
FILE_FORMAT = csv_format;

COPY INTO logistics_and_shipping
FROM @anycompany_lab.bronze.food_beverage_stage/logistics_and_shipping.csv
FILE_FORMAT = csv_format;

COPY INTO supplier_information
FROM @anycompany_lab.bronze.food_beverage_stage/supplier_information.csv
FILE_FORMAT = csv_format;

COPY INTO employee_records
FROM @anycompany_lab.bronze.food_beverage_stage/employee_records.csv
FILE_FORMAT = csv_format;

--Quand j'exécute la requête ci dessous j'obtiens un message d'erreur
COPY INTO product_reviews
FROM @anycompany_lab.bronze.food_beverage_stage/product_reviews.csv
FILE_FORMAT = csv_format;

--Pour la table product_reviews, j'ai ce message d'erreur quand j'essaye de copier les données : 
--Number of columns in file (8) does not match that of the corresponding table (9), use file format option error_on_column_count_mismatch=false to ignore this error File 'datasets/food-beverage/product_reviews.csv', line 3, character 1 Row 1 starts at line 2, column "PRODUCT_REVIEWS"["REVIEW_TEXT":8] If you would like to continue loading when an error is encountered, use other values such as 'SKIP_FILE' or 'CONTINUE' for the ON_ERROR option. For more information on loading options, please run 'info loading_data' in a SQL client.

--Je vérifie donc la structure réelle du fichier, avec la requête suivante :
SELECT 
    $1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7,
    $8,
FROM @anycompany_lab.bronze.food_beverage_stage/product_reviews.csv
(FILE_FORMAT => csv_format)
LIMIT 10; -- j'obtiens cette erreur : Found character 'J' instead of field delimiter ',' File 'datasets/food-beverage/product_reviews.csv', line 59, character 47 Row 56 starts at line 57, column "TRANSIENT_STAGE_TABLE"[45]
--Cela signifie que à la ligne 59, Snowflake pensait trouver une virgule, mais il a trouvé la lettre J → donc il considère que le format CSV est cassé.

--Solution trouvée
--Dans un premier temps, création d'une nouvelle table pour copier les données au format brut
CREATE OR REPLACE TABLE product_reviews_brute (
    line STRING
);

--Ensuite création d'un file_format pour la nouvelle table car en utilisant l'ancien (csv_format) on obtient une erreur : (Number of columns in file (8) does not match that of the corresponding table (1), use file format option error_on_column_count_mismatch=false to ignore this error File 'datasets/food-beverage/product_reviews.csv', line 3, character 1 Row 1 starts at line 2, column "PRODUCT_REVIEWS_BRUTE"[8] If you would like to continue loading when an error is encountered, use other values such as 'SKIP_FILE' or 'CONTINUE' for the ON_ERROR option. For more information on loading options, please run 'info loading_data' in a SQL client.)
CREATE OR REPLACE FILE FORMAT csv_format_brute
TYPE = CSV
FIELD_DELIMITER = 'NONE'
SKIP_HEADER = 1
TRIM_SPACE = FALSE;

--puis copie de la table sous format brute
COPY INTO product_reviews_brute
FROM @anycompany_lab.bronze.food_beverage_stage/product_reviews.csv
FILE_FORMAT = csv_format_brute;

--vérifier que la copie à bien été effectuer
select * from product_reviews_brute;

--Test pour visualiser la séparation des colonnes
SELECT
    SPLIT(line, '\t') AS cols
FROM product_reviews_brute
LIMIT 10;

--Parser proprement les données de la table product_reviews
INSERT INTO product_reviews
SELECT
    cols[0]::NUMBER                        AS review_id,
    cols[1]::STRING                        AS product_id,
    cols[2]::STRING                        AS reviewer_id,
    cols[3]::STRING                        AS reviewer_name,
    cols[6]::NUMBER                        AS rating,
    cols[7]::TIMESTAMP                     AS review_date,
    cols[8]::STRING                        AS review_title,
    cols[9]::STRING                        AS review_text,
    cols[11]::STRING                       AS product_category
FROM (
    SELECT SPLIT(line, '\t') AS cols
    FROM product_reviews_brute
);

--vérification
select * from product_reviews limit 10;


--Fichier .json
--file format
CREATE OR REPLACE FILE FORMAT json_format
TYPE = JSON;

--Étape 2 – Création des tables
CREATE OR REPLACE TABLE anycompany_lab.bronze.inventory (data VARIANT);
CREATE OR REPLACE TABLE anycompany_lab.bronze.store_locations (data VARIANT);

--Étape 3 – Chargement des données
COPY INTO inventory
FROM @anycompany_lab.bronze.food_beverage_stage/inventory.json
FILE_FORMAT = json_format;

COPY INTO store_locations
FROM @anycompany_lab.bronze.food_beverage_stage/store_locations.json
FILE_FORMAT = json_format;

--Étape 4 – Vérifications
---Vérifier le nombre de lignes
SELECT 'customer_demographics' AS table_name, COUNT(*) AS total_rows FROM customer_demographics
UNION ALL
SELECT 'customer_service_interactions', COUNT(*) FROM customer_service_interactions
UNION ALL
SELECT 'financial_transactions', COUNT(*) FROM financial_transactions
UNION ALL
SELECT 'promotions_data', COUNT(*) FROM promotions_data
UNION ALL
SELECT 'marketing_campaigns', COUNT(*) FROM marketing_campaigns
UNION ALL
SELECT 'product_reviews', COUNT(*) FROM product_reviews
UNION ALL
SELECT 'inventory', COUNT(*) FROM inventory
UNION ALL
SELECT 'store_locations', COUNT(*) FROM store_locations
UNION ALL
SELECT 'logistics_and_shipping', COUNT(*) FROM logistics_and_shipping
UNION ALL
SELECT 'supplier_information', COUNT(*) FROM supplier_information
UNION ALL
SELECT 'employee_records', COUNT(*) FROM employee_records;

--Résultat
/*
TABLE_NAME	                     TOTAL_ROWS
customer_demographics	          5000
customer_service_interactions	  5000
financial_transactions	          5000
promotions_data	                  87
marketing_campaigns	              5000
product_reviews	                  999
inventory	                      1
store_locations	                  1
logistics_and_shipping	          5000
supplier_information	          5000
employee_records	              5000
*/

----Inspecter un échantillon (SELECT * LIMIT 10)
-- Inspecter les clients
SELECT * FROM customer_demographics LIMIT 10;

-- Inspecter les interactions service client
SELECT * FROM customer_service_interactions LIMIT 10;

-- Inspecter les transactions financières
SELECT * FROM financial_transactions LIMIT 10;