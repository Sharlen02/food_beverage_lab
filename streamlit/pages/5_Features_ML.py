import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Features ML", layout="wide")
session = get_active_session()

st.title("🤖 Features ML : Schéma ANALYTICS")
st.markdown("Exploration du data product ML : tables enrichies, features clients et KPIs de vente.")

# ── Chargement des données ──────────────────────────────────────────────────

@st.cache_data
def load_sales_kpi():
    return session.sql("""
        SELECT *
        FROM ANYCOMPANY_LAB.ANALYTICS.SALES_KPI
        ORDER BY YEAR, MONTH, REGION
    """).to_pandas()

@st.cache_data
def load_customer_features():
    return session.sql("""
        SELECT *
        FROM ANYCOMPANY_LAB.ANALYTICS.CUSTOMER_FEATURES
    """).to_pandas()

@st.cache_data
def load_ventes_enrichies_sample():
    return session.sql("""
        SELECT *
        FROM ANYCOMPANY_LAB.ANALYTICS.VENTE_ENRICHIES
        LIMIT 500
    """).to_pandas()

@st.cache_data
def load_promotion_actives():
    return session.sql("""
        SELECT *
        FROM ANYCOMPANY_LAB.ANALYTICS.PROMOTION_ACTIVES
    """).to_pandas()

@st.cache_data
def load_promo_flag_impact():
    return session.sql("""
        SELECT
            PROMOTION_FLAG,
            MARKETING_FLAG,
            ROUND(AVG(AMOUNT), 2)   AS PANIER_MOYEN,
            COUNT(*)                AS NB_TRANSACTIONS,
            SUM(AMOUNT)             AS CA_TOTAL
        FROM ANYCOMPANY_LAB.ANALYTICS.VENTE_ENRICHIES
        GROUP BY PROMOTION_FLAG, MARKETING_FLAG
        ORDER BY PROMOTION_FLAG, MARKETING_FLAG
    """).to_pandas()

@st.cache_data
def load_features_by_age():
    return session.sql("""
        SELECT
            TRANCHE_AGE,
            ROUND(AVG(PANIER_MOYEN), 2)    AS PANIER_MOYEN_MOY,
            ROUND(AVG(TOTAL_DEPENSE), 2)   AS DEPENSE_MOYS,
            ROUND(AVG(PROMOTION_USAGE), 2) AS USAGE_PROMO_MOY,
            COUNT(*)                       AS NB_CLIENTS
        FROM ANYCOMPANY_LAB.ANALYTICS.CUSTOMER_FEATURES
        GROUP BY TRANCHE_AGE
        ORDER BY TRANCHE_AGE
    """).to_pandas()

@st.cache_data
def load_features_by_income():
    return session.sql("""
        SELECT
            TRANCHE_REVENUS,
            ROUND(AVG(PANIER_MOYEN), 2)    AS PANIER_MOYEN_MOY,
            ROUND(AVG(TOTAL_DEPENSE), 2)   AS DEPENSE_MOYS,
            ROUND(AVG(PROMOTION_USAGE), 2) AS USAGE_PROMO_MOY,
            COUNT(*)                       AS NB_CLIENTS
        FROM ANYCOMPANY_LAB.ANALYTICS.CUSTOMER_FEATURES
        GROUP BY TRANCHE_REVENUS
    """).to_pandas()

# ── Chargement ──────────────────────────────────────────────────────────────
with st.spinner("Chargement des tables ANALYTICS..."):
    df_kpi     = load_sales_kpi()
    df_cust    = load_customer_features()
    df_ventes  = load_ventes_enrichies_sample()
    df_promos  = load_promotion_actives()
    df_flags   = load_promo_flag_impact()
    df_age_ft  = load_features_by_age()
    df_inc_ft  = load_features_by_income()

# ── KPIs schéma ANALYTICS ───────────────────────────────────────────────────
st.subheader("Vue d'ensemble du schéma ANALYTICS")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Clients dans customer_features",  f"{len(df_cust):,}")
k2.metric("Transactions dans vente_enrichies", f"{len(df_ventes):,} (échantillon)")
k3.metric("Promotions dans promotion_actives", f"{len(df_promos):,}")
k4.metric("Lignes dans SALES_KPI",            f"{len(df_kpi):,}")

st.markdown("---")

# ── Architecture ─────────────────────────────────────────────────────────────
st.subheader("Architecture des tables ANALYTICS")

tables_info = {
    "Table": [
        "vente_enrichies", "client_enrichis",
        "customer_features", "promotion_actives", "SALES_KPI (vue)"
    ],
    "Type": ["Table", "Table", "Table", "Table", "Vue"],
    "Grain": [
        "1 ligne / transaction",
        "1 ligne / client",
        "1 ligne / client (agrégé)",
        "1 ligne / promotion",
        "1 ligne / région-année-mois"
    ],
    "Features clés": [
        "promotion_flag, campaign_flag, discount_pct",
        "tranche_age, tranche_revenus",
        "panier_moyen, promotion_usage, nombre_d_achat",
        "promotion_duration, discount_percentage",
        "total_sales, sales_with_promotion"
    ],
    "Usage ML": [
        "Attribution, impact promo",
        "Segmentation",
        "CLV, Churn, RFM",
        "Élasticité prix",
        "KPI temporels"
    ]
}
st.dataframe(pd.DataFrame(tables_info), use_container_width=True, hide_index=True)

st.markdown("---")

# ── Impact promotion_flag et campaign_flag ───────────────────────────────────
st.subheader("Impact des flags promo & campagne sur le panier moyen")

df_flags["LABEL"] = df_flags.apply(
    lambda r: f"Promo={'Oui' if r['PROMOTION_FLAG']==1 else 'Non'} / Camp={'Oui' if r['MARKETING_FLAG']==1 else 'Non'}",
    axis=1
)

c1, c2 = st.columns(2)
with c1:
    fig_pm = px.bar(
        df_flags,
        x="LABEL", y="PANIER_MOYEN",
        labels={"LABEL": "Combinaison", "PANIER_MOYEN": "Panier moyen (€)"},
        color="PANIER_MOYEN",
        color_continuous_scale=["#E1F5EE","#085041"],
        text_auto=True
    )
    fig_pm.update_layout(coloraxis_showscale=False, title="Panier moyen par combinaison flag", margin=dict(t=40))
    st.plotly_chart(fig_pm, use_container_width=True)

with c2:
    fig_vol = px.bar(
        df_flags,
        x="LABEL", y="NB_TRANSACTIONS",
        labels={"LABEL": "Combinaison", "NB_TRANSACTIONS": "Nb transactions"},
        color="NB_TRANSACTIONS",
        color_continuous_scale=["#E6F1FB","#042C53"],
        text_auto=True
    )
    fig_vol.update_layout(coloraxis_showscale=False, title="Volume de transactions", margin=dict(t=40))
    st.plotly_chart(fig_vol, use_container_width=True)

st.markdown("---")

# ── Features par tranche d'âge ───────────────────────────────────────────────
st.subheader("Distribution des features par tranche d'âge")

age_order = ["Under 25", "25-40", "41-60", "60+"]
df_age_ft["TRANCHE_AGE"] = pd.Categorical(df_age_ft["TRANCHE_AGE"], categories=age_order, ordered=True)
df_age_ft = df_age_ft.sort_values("TRANCHE_AGE")

tab1, tab2, tab3 = st.tabs(["Panier moyen", "Dépense totale moyenne", "Usage promos"])

with tab1:
    fig = px.bar(df_age_ft, x="TRANCHE_AGE", y="PANIER_MOYEN_MOY",
                 labels={"TRANCHE_AGE":"Tranche d'âge","PANIER_MOYEN_MOY":"Panier moyen (€)"},
                 color_discrete_sequence=["#7F77DD"], text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig = px.bar(df_age_ft, x="TRANCHE_AGE", y="DEPENSE_MOYS",
                 labels={"TRANCHE_AGE":"Tranche d'âge","DEPENSE_MOYS":"Dépense totale moy. (€)"},
                 color_discrete_sequence=["#1D9E75"], text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    fig = px.bar(df_age_ft, x="TRANCHE_AGE", y="USAGE_PROMO_MOY",
                 labels={"TRANCHE_AGE":"Tranche d'âge","USAGE_PROMO_MOY":"Usage promos moyen"},
                 color_discrete_sequence=["#D85A30"], text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Features par tranche de revenu ───────────────────────────────────────────
st.subheader("Distribution des features par tranche de revenu")

income_order = ["Low Income", "Middle Income", "High Income"]
df_inc_ft["TRANCHE_REVENUS"] = pd.Categorical(df_inc_ft["TRANCHE_REVENUS"], categories=income_order, ordered=True)
df_inc_ft = df_inc_ft.sort_values("TRANCHE_REVENUS")

fig_inc = go.Figure()
fig_inc.add_trace(go.Bar(name="Panier moyen (€)", x=df_inc_ft["TRANCHE_REVENUS"], y=df_inc_ft["PANIER_MOYEN_MOY"], marker_color="#378ADD"))
fig_inc.add_trace(go.Bar(name="Usage promos", x=df_inc_ft["TRANCHE_REVENUS"], y=df_inc_ft["USAGE_PROMO_MOY"], marker_color="#D85A30"))
fig_inc.update_layout(
    barmode="group",
    yaxis_title="Valeur",
    xaxis_title="Tranche de revenu",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=40)
)
st.plotly_chart(fig_inc, use_container_width=True)


st.markdown("---")

# ── SALES_KPI ────────────────────────────────────────────────────────────────
st.subheader("SALES_KPI — Ventes mensuelles par région")

if not df_kpi.empty:
    regions = ["Toutes"] + sorted(df_kpi["REGION"].unique().tolist())
    sel_region = st.selectbox("Filtrer par région", regions)
    df_kpi_f = df_kpi if sel_region == "Toutes" else df_kpi[df_kpi["REGION"] == sel_region]

    if "YEAR" in df_kpi_f.columns and "MONTH" in df_kpi_f.columns:
        df_kpi_f = df_kpi_f.copy()
        df_kpi_f["PERIODE"] = df_kpi_f["YEAR"].astype(str) + "-" + df_kpi_f["MONTH"].astype(str).str.zfill(2)

        fig_kpi = px.line(
            df_kpi_f.sort_values("PERIODE"),
            x="PERIODE", y="TOTAL_SALES",
            color="REGION" if sel_region == "Toutes" else None,
            labels={"PERIODE": "Période", "TOTAL_SALES": "Ventes totales (€)", "REGION": "Région"},
            markers=True
        )
        fig_kpi.update_layout(margin=dict(t=10))
        st.plotly_chart(fig_kpi, use_container_width=True)

    st.dataframe(
        df_kpi_f.rename(columns={
            "REGION": "Région",
            "YEAR": "Année",
            "MONTH": "Mois",
            "TOTAL_SALES": "CA total (€)",
            "AVG_SALES": "CA moyen (€)",
            "NUMBER_OF_SALES": "Nb ventes",
            "SALES_WITH_PROMOTION": "Avec promo"
        }),
        use_container_width=True,
        hide_index=True,
        height=300
    )
else:
    st.warning("La vue SALES_KPI est vide ou la table ANALYTICS.VENTE_ENRICHIES n'existe pas encore. Exécutez d'abord le notebook phase3_ML.")

st.markdown("---")

# ── Catalogue features ML ────────────────────────────────────────────────────
st.subheader("Catalogue des features ML recommandées")

features_catalog = pd.DataFrame({
    "Feature": [
        "panier_moyen","promotion_usage","nombre_d_achat","total_depense",
        "tranche_age","tranche_revenus","promotion_flag","campaign_flag",
        "discount_percentage","promotion_duration"
    ],
    "Table source": [
        "customer_features","customer_features","customer_features","customer_features",
        "client_enrichis","client_enrichis","vente_enrichies","vente_enrichies",
        "promotion_actives","promotion_actives"
    ],
    "Type": [
        "Numérique","Entier","Entier","Numérique",
        "Catégoriel","Catégoriel","Binaire","Binaire",
        "Numérique","Numérique"
    ],
    "Usage ML": [
        "CLV / Churn","Sensibilité promo","RFM / Churn","CLV",
        "Segmentation","Segmentation","Impact promo","Attribution",
        "Élasticité prix","Durée d'effet"
    ],
    "Priorité": [
        "Haute","Haute","Haute","Haute",
        "Moyenne","Moyenne","Haute","Haute",
        "Moyenne","Faible"
    ]
})

priority_colors = {"Haute": "🔴", "Moyenne": "🟡", "Faible": "🟢"}
features_catalog["Priorité"] = features_catalog["Priorité"].map(lambda x: f"{priority_colors[x]} {x}")

st.dataframe(features_catalog, use_container_width=True, hide_index=True)
st.caption("Priorité = importance estimée pour un premier modèle de prédiction de churn ou de CLV.")
