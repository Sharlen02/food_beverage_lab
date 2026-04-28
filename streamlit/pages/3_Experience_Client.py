import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Expérience Client", layout="wide")
session = get_active_session()

st.title("⭐ Expérience Client")
st.markdown("Analyse des avis produits, de la satisfaction SAV et de la segmentation démographique.")

# ── Chargement des données ──────────────────────────────────────────────────

@st.cache_data
def load_product_reviews():
    return session.sql("""
        SELECT
            PRODUCT_ID,
            PRODUCT_CATEGORY,
            ROUND(AVG(RATING), 2)  AS NOTE_MOYENNE,
            COUNT(REVIEW_ID)       AS NOMBRE_AVIS,
            CASE
                WHEN AVG(RATING) >= 4 THEN 'Excellent'
                WHEN AVG(RATING) >= 3 THEN 'Moyen'
                ELSE 'Critique'
            END AS STATUT_SATISFACTION
        FROM ANYCOMPANY_LAB.SILVER.PRODUCT_REVIEWS_CLEAN
        GROUP BY PRODUCT_ID, PRODUCT_CATEGORY
        ORDER BY NOTE_MOYENNE DESC
    """).to_pandas()

@st.cache_data
def load_reviews_by_category():
    return session.sql("""
        SELECT
            PRODUCT_CATEGORY,
            ROUND(AVG(RATING), 2) AS NOTE_MOYENNE,
            COUNT(*)              AS NB_AVIS
        FROM ANYCOMPANY_LAB.SILVER.PRODUCT_REVIEWS_CLEAN
        GROUP BY PRODUCT_CATEGORY
        ORDER BY NOTE_MOYENNE DESC
    """).to_pandas()

@st.cache_data
def load_sav():
    return session.sql("""
        SELECT
            ISSUE_CATEGORY,
            RESOLUTION_STATUS,
            COUNT(INTERACTION_ID)               AS NOMBRE_CAS,
            ROUND(AVG(CUSTOMER_SATISFACTION), 1) AS SATISFACTION_MOYENNE,
            CASE
                WHEN AVG(CUSTOMER_SATISFACTION) >= 4.5 THEN 'Exceptionnel'
                WHEN AVG(CUSTOMER_SATISFACTION) >= 3.8 THEN 'Satisfaisant'
                WHEN AVG(CUSTOMER_SATISFACTION) >= 3.0 THEN 'Moyennement satisfait'
                WHEN AVG(CUSTOMER_SATISFACTION) >= 2.0 THEN 'Insatisfaisant'
                ELSE 'Critique'
            END AS APPRECIATION_CLIENT
        FROM ANYCOMPANY_LAB.SILVER.CUSTOMER_SERVICE_INTERACTIONS_CLEAN
        GROUP BY ISSUE_CATEGORY, RESOLUTION_STATUS
        ORDER BY NOMBRE_CAS DESC
    """).to_pandas()

@st.cache_data
def load_demo_gender():
    return session.sql("""
        SELECT GENDER, COUNT(*) AS NB_CLIENTS
        FROM ANYCOMPANY_LAB.SILVER.CUSTOMER_DEMOGRAPHICS_CLEAN
        GROUP BY GENDER
    """).to_pandas()

@st.cache_data
def load_demo_age():
    return session.sql("""
        SELECT
            CASE
                WHEN DATEDIFF(YEAR, DATE_OF_BIRTH, CURRENT_DATE) < 25  THEN 'Under 25'
                WHEN DATEDIFF(YEAR, DATE_OF_BIRTH, CURRENT_DATE) BETWEEN 25 AND 40 THEN '25-40'
                WHEN DATEDIFF(YEAR, DATE_OF_BIRTH, CURRENT_DATE) BETWEEN 41 AND 60 THEN '41-60'
                ELSE '60+'
            END AS TRANCHE_AGE,
            COUNT(*) AS NB_CLIENTS
        FROM ANYCOMPANY_LAB.SILVER.CUSTOMER_DEMOGRAPHICS_CLEAN
        GROUP BY TRANCHE_AGE
        ORDER BY TRANCHE_AGE
    """).to_pandas()

@st.cache_data
def load_demo_income():
    return session.sql("""
        SELECT
            CASE
                WHEN ANNUAL_INCOME < 30000               THEN 'Low Income'
                WHEN ANNUAL_INCOME BETWEEN 30000 AND 70000 THEN 'Middle Income'
                ELSE 'High Income'
            END AS TRANCHE_REVENUS,
            COUNT(*) AS NB_CLIENTS
        FROM ANYCOMPANY_LAB.SILVER.CUSTOMER_DEMOGRAPHICS_CLEAN
        GROUP BY TRANCHE_REVENUS
    """).to_pandas()

@st.cache_data
def load_demo_age_income():
    return session.sql("""
        SELECT
            CASE
                WHEN ANNUAL_INCOME < 30000               THEN 'Low Income'
                WHEN ANNUAL_INCOME BETWEEN 30000 AND 70000 THEN 'Middle Income'
                ELSE 'High Income'
            END AS TRANCHE_REVENUS,
            CASE
                WHEN DATEDIFF(YEAR, DATE_OF_BIRTH, CURRENT_DATE()) < 25  THEN 'Under 25'
                WHEN DATEDIFF(YEAR, DATE_OF_BIRTH, CURRENT_DATE()) BETWEEN 25 AND 40 THEN '25-40'
                WHEN DATEDIFF(YEAR, DATE_OF_BIRTH, CURRENT_DATE()) BETWEEN 41 AND 60 THEN '41-60'
                ELSE '60+'
            END AS TRANCHE_AGE,
            COUNT(*) AS NB_CLIENTS
        FROM ANYCOMPANY_LAB.SILVER.CUSTOMER_DEMOGRAPHICS_CLEAN
        GROUP BY TRANCHE_REVENUS, TRANCHE_AGE
        ORDER BY TRANCHE_REVENUS, TRANCHE_AGE
    """).to_pandas()

@st.cache_data
def load_demo_region():
    return session.sql("""
        SELECT REGION, COUNT(*) AS NB_CLIENTS
        FROM ANYCOMPANY_LAB.SILVER.CUSTOMER_DEMOGRAPHICS_CLEAN
        GROUP BY REGION
        ORDER BY NB_CLIENTS DESC
    """).to_pandas()

# ── Chargement ──────────────────────────────────────────────────────────────
with st.spinner("Chargement des données clients..."):
    df_reviews   = load_product_reviews()
    df_rev_cat   = load_reviews_by_category()
    df_sav       = load_sav()
    df_gender    = load_demo_gender()
    df_age       = load_demo_age()
    df_income    = load_demo_income()
    df_age_inc   = load_demo_age_income()
    df_region    = load_demo_region()

# ── KPIs ────────────────────────────────────────────────────────────────────
st.subheader("Indicateurs clés")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Note moyenne globale",   f"{df_reviews['NOTE_MOYENNE'].mean():.2f} / 5")
k2.metric("Total avis",             f"{df_reviews['NOMBRE_AVIS'].sum():,}")
pct_ex = (df_reviews['STATUT_SATISFACTION'] == 'Excellent').mean() * 100
k3.metric("Produits 'Excellent'",   f"{pct_ex:.0f}%")
pct_cr = (df_reviews['STATUT_SATISFACTION'] == 'Critique').mean() * 100
k4.metric("Produits critiques",     f"{pct_cr:.0f}%")

st.markdown("---")

# ── Avis produits ────────────────────────────────────────────────────────────
st.subheader("Avis produits")
tab1, tab2 = st.tabs(["Par catégorie", "Par produit (Top/Flop)"])

with tab1:
    fig_cat = px.bar(
        df_rev_cat,
        x="NOTE_MOYENNE", y="PRODUCT_CATEGORY",
        orientation="h",
        labels={"NOTE_MOYENNE": "Note moyenne", "PRODUCT_CATEGORY": "Catégorie"},
        color="NOTE_MOYENNE",
        color_continuous_scale=["#FCEBEB", "#1D9E75"],
        range_color=[1, 5],
        text_auto=True
    )
    fig_cat.update_layout(coloraxis_showscale=False, margin=dict(t=10))
    st.plotly_chart(fig_cat, use_container_width=True)

with tab2:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Top 10 produits les mieux notés**")
        st.dataframe(
            df_reviews.head(10)[["PRODUCT_ID","PRODUCT_CATEGORY","NOTE_MOYENNE","NOMBRE_AVIS","STATUT_SATISFACTION"]]
            .rename(columns={"PRODUCT_ID":"ID","PRODUCT_CATEGORY":"Catégorie",
                              "NOTE_MOYENNE":"Note","NOMBRE_AVIS":"Avis","STATUT_SATISFACTION":"Statut"}),
            use_container_width=True, hide_index=True
        )
    with col_b:
        st.markdown("**Flop 10 produits les moins bien notés**")
        st.dataframe(
            df_reviews.tail(10)[["PRODUCT_ID","PRODUCT_CATEGORY","NOTE_MOYENNE","NOMBRE_AVIS","STATUT_SATISFACTION"]]
            .rename(columns={"PRODUCT_ID":"ID","PRODUCT_CATEGORY":"Catégorie",
                              "NOTE_MOYENNE":"Note","NOMBRE_AVIS":"Avis","STATUT_SATISFACTION":"Statut"}),
            use_container_width=True, hide_index=True
        )

st.markdown("---")

# ── SAV ──────────────────────────────────────────────────────────────────────
st.subheader("Satisfaction Service Client (SAV)")

color_map = {
    "Exceptionnel": "#1D9E75",
    "Satisfaisant": "#378ADD",
    "Moyennement satisfait": "#BA7517",
    "Insatisfaisant": "#D85A30",
    "Critique": "#E24B4A"
}

c1, c2 = st.columns([2, 1])
with c1:
    fig_sav = px.bar(
        df_sav,
        x="SATISFACTION_MOYENNE", y="ISSUE_CATEGORY",
        color="RESOLUTION_STATUS",
        orientation="h",
        barmode="group",
        labels={
            "SATISFACTION_MOYENNE": "Satisfaction moyenne",
            "ISSUE_CATEGORY": "Catégorie",
            "RESOLUTION_STATUS": "Statut résolution"
        },
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_sav.update_layout(xaxis_range=[0, 5], margin=dict(t=10))
    st.plotly_chart(fig_sav, use_container_width=True)

with c2:
    st.dataframe(
        df_sav.rename(columns={
            "ISSUE_CATEGORY": "Catégorie",
            "RESOLUTION_STATUS": "Statut",
            "NOMBRE_CAS": "Cas",
            "SATISFACTION_MOYENNE": "Satisfaction",
            "APPRECIATION_CLIENT": "Appréciation"
        }),
        use_container_width=True,
        hide_index=True
    )

st.markdown("---")

# ── Segmentation démographique ───────────────────────────────────────────────
st.subheader("Segmentation démographique des clients")
d1, d2, d3 = st.columns(3)

with d1:
    fig_g = px.pie(
        df_gender, values="NB_CLIENTS", names="GENDER",
        title="Répartition par genre",
        color_discrete_sequence=["#7F77DD", "#1D9E75", "#D85A30"]
    )
    fig_g.update_layout(margin=dict(t=40))
    st.plotly_chart(fig_g, use_container_width=True)

with d2:
    age_order = ["Under 25", "25-40", "41-60", "60+"]
    df_age["TRANCHE_AGE"] = pd.Categorical(df_age["TRANCHE_AGE"], categories=age_order, ordered=True)
    df_age = df_age.sort_values("TRANCHE_AGE")
    fig_a = px.bar(
        df_age, x="TRANCHE_AGE", y="NB_CLIENTS",
        title="Répartition par tranche d'âge",
        labels={"TRANCHE_AGE": "Tranche", "NB_CLIENTS": "Clients"},
        color="NB_CLIENTS", color_continuous_scale=["#E6F1FB","#0C447C"]
    )
    fig_a.update_layout(coloraxis_showscale=False, margin=dict(t=40))
    st.plotly_chart(fig_a, use_container_width=True)

with d3:
    fig_i = px.pie(
        df_income, values="NB_CLIENTS", names="TRANCHE_REVENUS",
        title="Répartition par revenu",
        color_discrete_sequence=["#1D9E75", "#378ADD", "#BA7517"]
    )
    fig_i.update_layout(margin=dict(t=40))
    st.plotly_chart(fig_i, use_container_width=True)

# ── Croisement âge × revenu ──────────────────────────────────────────────────
st.subheader("Croisement âge × revenu")
fig_heatmap = px.density_heatmap(
    df_age_inc,
    x="TRANCHE_AGE", y="TRANCHE_REVENUS", z="NB_CLIENTS",
    labels={"TRANCHE_AGE":"Tranche d'âge","TRANCHE_REVENUS":"Tranche de revenu","NB_CLIENTS":"Nb clients"},
    color_continuous_scale="Blues",
    text_auto=True,
    category_orders={"TRANCHE_AGE": ["Under 25","25-40","41-60","60+"]}
)
fig_heatmap.update_layout(margin=dict(t=20))
st.plotly_chart(fig_heatmap, use_container_width=True)

# ── Clients par région ───────────────────────────────────────────────────────
st.subheader("Clients par région")
fig_reg = px.bar(
    df_region,
    x="NB_CLIENTS", y="REGION",
    orientation="h",
    labels={"NB_CLIENTS":"Nombre de clients","REGION":"Région"},
    color="NB_CLIENTS",
    color_continuous_scale=["#FAEEDA","#412402"]
)
fig_reg.update_layout(coloraxis_showscale=False, margin=dict(t=10))
st.plotly_chart(fig_reg, use_container_width=True)
