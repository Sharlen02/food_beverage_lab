USE DATABASE anycompany_lab;
USE SCHEMA SILVER;

-- Clean de la table customer_demographics

CREATE OR REPLACE TABLE SILVER.CUSTOMER_DEMOGRAPHICS_CLEAN AS
SELECT
    customer_id,
    TRIM(name) AS name,
    TRY_TO_DATE(date_of_birth) AS date_of_birth,
    TRIM(gender) AS gender,
    TRIM(region) AS region,
    TRIM(country) AS country,
    TRIM(city) AS city,
    TRIM(marital_status) AS marital_status,
    TRY_TO_NUMBER(REPLACE(annual_income, ' ', ''), 12, 0) AS annual_income
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY customer_id) AS rn
    FROM BRONZE.CUSTOMER_DEMOGRAPHICS
    WHERE customer_id IS NOT NULL
)
WHERE rn = 1;


SELECT * FROM silver.customer_demographics_clean;

-- Clean de la table customer_service_interactions

CREATE OR REPLACE TABLE SILVER.CUSTOMER_SERVICE_INTERACTIONS_CLEAN AS
SELECT
    interaction_id,
    interaction_date,
    interaction_type,
    issue_category,
    description,
    duration_minutes,
    resolution_status,
    follow_up_required,
    customer_satisfaction
FROM BRONZE.CUSTOMER_SERVICE_INTERACTIONS;
  
-- Check 
SELECT * from customer_service_interactions_clean;
SELECT count (*) from customer_service_interactions_clean;
  

-- Clean de la table financial_transactions
CREATE OR REPLACE TABLE SILVER.FINANCIAL_TRANSACTIONS_CLEAN AS
SELECT
    transaction_id,
    transaction_date,
    TRIM(transaction_type) AS transaction_type,
    ABS(amount) AS amount,
    TRIM(payment_method) AS payment_method,
    TRIM(entity) AS entity,
    TRIM(region) AS region,
    TRIM(account_code) AS account_code
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY transaction_date DESC) rn
    FROM BRONZE.financial_transactions
)
WHERE rn = 1;

-- CHECK
SELECT * From financial_transactions_clean; 

-- Clean de la table promotions_data (Supprimer les lignes où dans la colonne 'REGION' on retrouve les valeurs 0 et 1)

CREATE OR REPLACE TABLE SILVER.PROMOTIONS_DATA_CLEAN AS
SELECT
    promotion_id,
    TRIM(product_category) AS product_category,
    TRIM(promotion_type) AS promotion_type,
    discount_percentage,
    start_date,
    end_date,
    TRIM(region) AS region
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY promotion_id ORDER BY start_date DESC) rn
    FROM BRONZE.promotions_data
)
WHERE rn = 1
AND (start_date <= end_date OR start_date IS NULL OR end_date IS NULL)
AND TRIM(region) NOT IN ('0', '1');

select * from PROMOTIONS_DATA_CLEAN;
select count(*) from PROMOTIONS_DATA_CLEAN; -->87 lignes avant nettoyage; 83 lignes après nettoyage

-- Clean de la table marketing_campaigns

CREATE OR REPLACE TABLE SILVER.MARKETING_CAMPAIGNS_CLEAN AS
SELECT
    campaign_id,
    campaign_name,
    campaign_type,
    product_category,
    target_audience,
    start_date,
    end_date,
    region,
    budget,
    reach,
    conversion_rate
FROM BRONZE.marketing_campaigns;

-- CHECK
SELECT count (*) from marketing_campaigns_clean; -->5 000 lignes
SELECT * from marketing_campaigns_clean;


-- Clean de la table product_reviews (Modifie la colonne 'review_date' de ce format : "2024-06-16 08:40:06.000" en ce format : "2024-06-16)

CREATE OR REPLACE TABLE SILVER.PRODUCT_REVIEWS_CLEAN AS
SELECT
    review_id,
    TRIM(product_id) AS product_id,
    TRIM(reviewer_id) AS reviewer_id,
    TRIM(reviewer_name) AS reviewer_name,
    rating,
    review_date::DATE AS review_date,
    TRIM(review_title) AS review_title,
    TRIM(review_text) AS review_text,
    TRIM(product_category) AS product_category
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY review_id ORDER BY review_date DESC) rn
    FROM BRONZE.product_reviews
)
WHERE rn = 1;

-- Check
Select count (*) from product_reviews_clean; --> 999 lignes
Select * from product_reviews_clean;


-- Clean logistics_and_shipping

CREATE OR REPLACE TABLE SILVER.LOGISTICS_AND_SHIPPING_CLEAN AS
SELECT
    shipment_id,
    order_id,
    ship_date,
    estimated_delivery,
    TRIM(shipping_method) AS shipping_method,
    TRIM(status) AS status,
    shipping_cost,
    NULLIF(TRIM(destination_region), '') AS destination_region,
    NULLIF(TRIM(destination_country), '') AS destination_country,
    NULLIF(TRIM(carrier), '') AS carrier
FROM BRONZE.logistics_and_shipping;

-- Check
Select count (*) from logistics_and_shipping_clean;
Select * from logistics_and_shipping_clean;

-- Clean de la table supplier_information

CREATE OR REPLACE TABLE SILVER.SUPPLIER_INFORMATION_CLEAN AS
SELECT
    supplier_id,
    supplier_name,
    product_category,
    region,
    country,
    city,
    lead_time,
    reliability_score,
    quality_rating
FROM BRONZE.supplier_information;

-- Check
Select * from supplier_information_clean;


-- Clean  de la table employee_records

CREATE OR REPLACE TABLE SILVER.EMPLOYEE_RECORDS_CLEAN AS
SELECT
    employee_id,
    TRIM(name) AS name,
    date_of_birth,
    hire_date,
    TRIM(department) AS department,
    TRIM(job_title) AS job_title,
    salary,
    TRIM(region) AS region,
    TRIM(country) AS country,
    LOWER(TRIM(email)) AS email
FROM BRONZE.employee_records;

-- Check
Select count (*) from employee_records_clean;
Select * from employee_records_clean;



-- Clean de la table store locations 

CREATE OR REPLACE TABLE SILVER.STORE_LOCATIONS_CLEAN AS
SELECT
    f.value:store_id::STRING AS store_id,
    f.value:store_name::STRING AS store_name,
    f.value:store_type::STRING AS store_type,
    f.value:region::STRING AS region,
    f.value:country::STRING AS country,
    f.value:city::STRING AS city,
    f.value:address::STRING AS address,
    f.value:postal_code::NUMBER AS postal_code,
    f.value:square_footage::FLOAT AS square_footage,
    f.value:employee_count::NUMBER AS employee_count
FROM BRONZE.store_locations,
LATERAL FLATTEN(input => data) f;

-- Check
Select * from store_locations_clean;


-- Clean de la table inventory 

CREATE OR REPLACE TABLE SILVER.INVENTORY_CLEAN AS
SELECT
    f.value:product_id::STRING AS product_id,
    f.value:product_category::STRING AS product_category,
    f.value:region::STRING AS region,
    f.value:country::STRING AS country,
    f.value:warehouse::STRING AS warehouse,
    f.value:current_stock::NUMBER AS current_stock,
    f.value:reorder_point::NUMBER AS reorder_point,
    f.value:lead_time::NUMBER AS lead_time,
    f.value:last_restock_date::DATE AS last_restock_date
FROM BRONZE.inventory,
LATERAL FLATTEN(input => data) f;

-- Check
Select * from inventory_clean;

---------------

---Vérifier le nombre de lignes des tables SILVER avant mise à jour
SELECT 'CUSTOMER_DEMOGRAPHICS_CLEAN' AS table_name, COUNT(*) AS total_rows FROM customer_demographics_clean
UNION ALL
SELECT 'customer_service_interactions_clean', COUNT(*) FROM customer_service_interactions_clean
UNION ALL
SELECT 'financial_transactions_clean', COUNT(*) FROM financial_transactions_clean
UNION ALL
SELECT 'promotions_data_clean', COUNT(*) FROM promotions_data_clean
UNION ALL
SELECT 'marketing_campaigns_clean', COUNT(*) FROM marketing_campaigns_clean
UNION ALL
SELECT 'product_reviews_clean', COUNT(*) FROM product_reviews_clean
UNION ALL
SELECT 'inventory_clean', COUNT(*) FROM inventory_clean
UNION ALL
SELECT 'store_locations_clean', COUNT(*) FROM store_locations_clean
UNION ALL
SELECT 'logistics_and_shipping_clean', COUNT(*) FROM logistics_and_shipping_clean
UNION ALL
SELECT 'supplier_information_clean', COUNT(*) FROM supplier_information_clean
UNION ALL
SELECT 'employee_records_clean', COUNT(*) FROM employee_records_clean;

--résultat (--Le nombre de lignes des tables SILVER après mise à jour)
/*
TABLE_NAME                          	TOTAL_ROWS
CUSTOMER_DEMOGRAPHICS_CLEAN	            5 000
customer_service_interactions_clean	    5 000
financial_transactions_clean	        5 000
promotions_data_clean	                   83
marketing_campaigns_clean	            5 000
product_reviews_clean	                  999
inventory_clean	                        5 000
store_locations_clean	                5 000
logistics_and_shipping_clean	        5 000
supplier_information_clean	            5 000
employee_records_clean	                5 000
*/