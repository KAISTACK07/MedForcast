-- ============================================================================
-- Pharma Analytics Platform — Database Schema
-- ============================================================================
-- Creates all tables with proper foreign key relationships.
-- Run: psql -U postgres -d pharma_analytics -f schema.sql
-- ============================================================================

-- Drop tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS promotion_campaigns CASCADE;
DROP TABLE IF EXISTS prescriptions CASCADE;
DROP TABLE IF EXISTS rep_activity CASCADE;
DROP TABLE IF EXISTS pharma_sales CASCADE;
DROP TABLE IF EXISTS hcp_master CASCADE;
DROP TABLE IF EXISTS territories CASCADE;
DROP TABLE IF EXISTS drug_reference CASCADE;

-- ── Drug Reference ────────────────────────────────────────────────────────────
CREATE TABLE drug_reference (
    drug_id         SERIAL PRIMARY KEY,
    brand_name      VARCHAR(200) NOT NULL,
    generic_name    VARCHAR(200),
    manufacturer    VARCHAR(200),
    product_type    VARCHAR(100),
    route           VARCHAR(100),
    pharm_class     VARCHAR(200)
);

CREATE INDEX idx_drug_brand ON drug_reference(brand_name);

-- ── Territories ───────────────────────────────────────────────────────────────
CREATE TABLE territories (
    territory_id        VARCHAR(10) PRIMARY KEY,
    territory_name      VARCHAR(100) NOT NULL,
    region              VARCHAR(50) NOT NULL,
    state_coverage      TEXT,
    assigned_rep_count  INT DEFAULT 0,
    target_hcp_count    INT DEFAULT 0,
    annual_quota        NUMERIC(14, 2) DEFAULT 0
);

CREATE INDEX idx_territory_region ON territories(region);

-- ── HCP Master ────────────────────────────────────────────────────────────────
CREATE TABLE hcp_master (
    hcp_id                  VARCHAR(10) PRIMARY KEY,
    first_name              VARCHAR(100),
    last_name               VARCHAR(100),
    specialty               VARCHAR(100),
    tier                    VARCHAR(20),
    years_experience        INT,
    hospital_affiliation    VARCHAR(200),
    city                    VARCHAR(100),
    state                   VARCHAR(10),
    territory_id            VARCHAR(10) REFERENCES territories(territory_id),
    npi_number              BIGINT UNIQUE
);

CREATE INDEX idx_hcp_territory ON hcp_master(territory_id);
CREATE INDEX idx_hcp_specialty ON hcp_master(specialty);
CREATE INDEX idx_hcp_tier ON hcp_master(tier);

-- ── Pharma Sales ──────────────────────────────────────────────────────────────
CREATE TABLE pharma_sales (
    sale_id         SERIAL PRIMARY KEY,
    sale_date       DATE NOT NULL,
    drug_name       VARCHAR(200),
    territory_id    VARCHAR(10) REFERENCES territories(territory_id),
    units_sold      INT,
    unit_price      NUMERIC(10, 2),
    revenue         NUMERIC(14, 2)
);

CREATE INDEX idx_sales_date ON pharma_sales(sale_date);
CREATE INDEX idx_sales_territory ON pharma_sales(territory_id);
CREATE INDEX idx_sales_drug ON pharma_sales(drug_name);

-- ── Rep Activity ──────────────────────────────────────────────────────────────
CREATE TABLE rep_activity (
    activity_id         SERIAL PRIMARY KEY,
    rep_id              VARCHAR(10) NOT NULL,
    rep_name            VARCHAR(200),
    territory_id        VARCHAR(10) REFERENCES territories(territory_id),
    hcp_id              VARCHAR(10) REFERENCES hcp_master(hcp_id),
    activity_type       VARCHAR(50),
    activity_date       DATE,
    duration_minutes    INT,
    samples_left        INT DEFAULT 0,
    outcome             VARCHAR(50)
);

CREATE INDEX idx_rep_activity_rep ON rep_activity(rep_id);
CREATE INDEX idx_rep_activity_hcp ON rep_activity(hcp_id);
CREATE INDEX idx_rep_activity_date ON rep_activity(activity_date);

-- ── Prescriptions ─────────────────────────────────────────────────────────────
CREATE TABLE prescriptions (
    prescription_id     VARCHAR(20) PRIMARY KEY,
    hcp_id              VARCHAR(10) REFERENCES hcp_master(hcp_id),
    drug_name           VARCHAR(200),
    therapeutic_class   VARCHAR(200),
    prescription_date   DATE,
    quantity            INT,
    unit_price          NUMERIC(10, 2),
    total_value         NUMERIC(14, 2)
);

CREATE INDEX idx_rx_hcp ON prescriptions(hcp_id);
CREATE INDEX idx_rx_drug ON prescriptions(drug_name);
CREATE INDEX idx_rx_date ON prescriptions(prescription_date);

-- ── Promotion Campaigns ───────────────────────────────────────────────────────
CREATE TABLE promotion_campaigns (
    campaign_id             VARCHAR(20) PRIMARY KEY,
    campaign_name           VARCHAR(200),
    drug_name               VARCHAR(200),
    channel                 VARCHAR(50),
    start_date              DATE,
    end_date                DATE,
    budget                  NUMERIC(14, 2),
    hcps_targeted           INT,
    hcps_reached            INT,
    prescriptions_before    INT,
    prescriptions_after     INT,
    revenue_before          NUMERIC(14, 2),
    revenue_after           NUMERIC(14, 2)
);

CREATE INDEX idx_promo_drug ON promotion_campaigns(drug_name);
CREATE INDEX idx_promo_channel ON promotion_campaigns(channel);

-- ── Verify ────────────────────────────────────────────────────────────────────
SELECT 'Schema created successfully!' AS status;
