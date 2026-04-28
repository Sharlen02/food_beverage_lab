import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Marketing", layout="wide")
session = get_active_session()

st.title("📣 Marketing & Performance Commerciale")
st.markdown("Analyse des campagnes, ROI, efficacité et lien avec les ventes.")

# ── Chargement des données ──────────────────────────────────────────────────

@st.cache_data
def load_campaign_performance():
    return session.sql("""
        SELECT
            CAMPAIGN_NAME,
            CAMPAIGN_TYPE,
            PRODUCT_CATEGORY,
            BUDGET,
            ROUND(REACH * CONVERSION_RATE, 0)              AS ESTIMATIONS_CONVERSIONS,
            ROUND((REACH * CONVERSION_RATE) * 15, 2)       AS REVENU_ESTIME,
            ROUND(((REACH * CONVERSION_RATE) * 15)
                  / NULLIF(BUDGET, 0), 2)                  AS RATIO_PERFORMANCE
        FROM ANYCOMPANY_LAB.SILVER.MARKETING_CAMPAIGNS_CLEAN
        WHERE BUDGET > 0
        ORDER BY REVENU_ESTIME DESC
        LIMIT 50
    """).to_pandas()

@st.cache_data
def load_efficiency():
    return session.sql("""
        SELECT
            CAMPAIGN_NAME,
            CAMPAIGN_TYPE,
            BUDGET,
            ROUND((REACH * CONVERSION_RATE) / NULLIF(BUDGET, 0), 4) AS EFFICIENCY_SCORE,
            ROUND(BUDGET / NULLIF((REACH * CONVERSION_RATE), 0), 2)  AS COST_PER_CONVERSION,
            ROUND(REACH * CONVERSION_RATE, 0)                        AS ESTIMATED_CONVERSIONS
        FROM ANYCOMPANY_LAB.SILVER.MARKETING_CAMPAIGNS_CLEAN
        WHERE BUDGET > 0
          AND (REACH * CONVERSION_RATE) > 0
        ORDER BY EFFICIENCY_SCORE DESC
        LIMIT 20
    """).to_pandas()

@st.cache_data
def load_by_type():
    return session.sql("""
        SELECT
            CAMPAIGN_TYPE,
            SUM(BUDGET)              AS TOTAL_BUDGET,
            SUM(REACH)               AS TOTAL_REACH,
            ROUND(AVG(CONVERSION_RATE) * 100, 2) AS TAUX_CONVERSION_PCT,
            COUNT(*)                 AS NB_CAMPAGNES
        FROM ANYCOMPANY_LAB.SILVER.MARKETING_CAMPAIGNS_CLEAN
        GROUP BY CAMPAIGN_TYPE
        ORDER BY TOTAL_BUDGET DESC
    """).to_pandas()

@st.cache_data
def load_by_region():
    return session.sql("""
        SELECT
            REGION,
            ROUND(AVG(DISCOUNT_PERCENTAGE), 2) AS REMISE_MOYENNE,
            COUNT(*)                           AS NB_PROMOTIONS
        FROM ANYCOMPANY_LAB.SILVER.PROMOTIONS_DATA_CLEAN
        GROUP BY REGION
        ORDER BY REMISE_MOYENNE DESC
    """).to_pandas()

@st.cache_data
def load_campaign_sales_link():
    return session.sql("""
        SELECT
            M.CAMPAIGN_TYPE,
            M.REGION,
            SUM(F.AMOUNT) AS VENTES_PERIODE_CAMPAGNE
        FROM ANYCOMPANY_LAB.SILVER.MARKETING_CAMPAIGNS_CLEAN M
        JOIN ANYCOMPANY_LAB.SILVER.FINANCIAL_TRANSACTIONS_CLEAN F
            ON M.REGION = F.REGION
            AND F.TRANSACTION_DATE BETWEEN M.START_DATE AND M.END_DATE
        WHERE F.TRANSACTION_TYPE = 'Sale'
        GROUP BY M.CAMPAIGN_TYPE, M.REGION
        ORDER BY VENTES_PERIODE_CAMPAGNE DESC
    """).to_pandas()

# ── Chargement ──────────────────────────────────────────────────────────────
with st.spinner("Chargement des données marketing..."):
    df_perf   = load_campaign_performance()
    df_eff    = load_efficiency()
    df_type   = load_by_type()
    df_region = load_by_region()
    df_link   = load_campaign_sales_link()

# ── KPIs ────────────────────────────────────────────────────────────────────
st.subheader("Indicateurs clés")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Budget total",        f"€{df_type['TOTAL_BUDGET'].sum():,.0f}")
k2.metric("Nombre de campagnes", f"{df_type['NB_CAMPAGNES'].sum():,}")
k3.metric("Reach total estimé",  f"{df_type['TOTAL_REACH'].sum():,.0f}")
best_type = df_type.sort_values("TAUX_CONVERSION_PCT", ascending=False).iloc[0]
k4.metric("Meilleur type (conv.)", f"{best_type['CAMPAIGN_TYPE']} — {best_type['TAUX_CONVERSION_PCT']:.1f}%")

st.markdown("---")

# ── Budget et conversion par type ───────────────────────────────────────────
st.subheader("Budget et taux de conversion par type de campagne")
c1, c2 = st.columns(2)

with c1:
    fig_budget = px.bar(
        df_type,
        x="CAMPAIGN_TYPE", y="TOTAL_BUDGET",
        labels={"CAMPAIGN_TYPE": "Type", "TOTAL_BUDGET": "Budget (€)"},
        color="TOTAL_BUDGET",
        color_continuous_scale=["#E6F1FB", "#0C447C"],
        text_auto=True
    )
    fig_budget.update_layout(coloraxis_showscale=False, title="Budget par type de canal", margin=dict(t=40))
    st.plotly_chart(fig_budget, use_container_width=True)

with c2:
    fig_conv = px.bar(
        df_type,
        x="CAMPAIGN_TYPE", y="TAUX_CONVERSION_PCT",
        labels={"CAMPAIGN_TYPE": "Type", "TAUX_CONVERSION_PCT": "Taux conversion (%)"},
        color="TAUX_CONVERSION_PCT",
        color_continuous_scale=["#E1F5EE", "#085041"],
        text_auto=True
    )
    fig_conv.update_layout(coloraxis_showscale=False, title="Taux de conversion (%)", margin=dict(t=40))
    st.plotly_chart(fig_conv, use_container_width=True)

st.markdown("---")

# ── Top campagnes efficaces ──────────────────────────────────────────────────
st.subheader("Top 20 campagnes les plus efficaces")
st.caption("Score d'efficacité = Conversions estimées / Budget. Plus le score est élevé, plus la campagne est rentable.")

fig_eff = px.scatter(
    df_eff,
    x="BUDGET", y="EFFICIENCY_SCORE",
    size="ESTIMATED_CONVERSIONS",
    color="CAMPAIGN_TYPE",
    hover_name="CAMPAIGN_NAME",
    hover_data={"COST_PER_CONVERSION": True},
    labels={
        "BUDGET": "Budget (€)",
        "EFFICIENCY_SCORE": "Score d'efficacité",
        "CAMPAIGN_TYPE": "Type"
    },
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_eff.update_layout(margin=dict(t=20))
st.plotly_chart(fig_eff, use_container_width=True)

with st.expander("Voir le détail des 20 campagnes"):
    st.dataframe(
        df_eff.rename(columns={
            "CAMPAIGN_NAME": "Campagne",
            "CAMPAIGN_TYPE": "Type",
            "BUDGET": "Budget (€)",
            "EFFICIENCY_SCORE": "Score efficacité",
            "COST_PER_CONVERSION": "Coût / conversion (€)",
            "ESTIMATED_CONVERSIONS": "Conv. estimées"
        }),
        use_container_width=True,
        hide_index=True
    )

st.markdown("---")

# ── Lien campagnes / ventes ──────────────────────────────────────────────────
st.subheader("Ventes réalisées pendant les périodes de campagne")
st.caption("Jointure par région et date : transactions enregistrées dans la fenêtre d'une campagne active.")

fig_link = px.bar(
    df_link,
    x="VENTES_PERIODE_CAMPAGNE", y="REGION",
    orientation="h",
    color="CAMPAIGN_TYPE",
    labels={
        "VENTES_PERIODE_CAMPAGNE": "Ventes (€)",
        "REGION": "Région",
        "CAMPAIGN_TYPE": "Type de campagne"
    },
    color_discrete_sequence=px.colors.qualitative.Pastel
)
fig_link.update_layout(margin=dict(t=20))
st.plotly_chart(fig_link, use_container_width=True)

st.markdown("---")

# ── Promotions par région ────────────────────────────────────────────────────
st.subheader("Effort promotionnel par région")
c3, c4 = st.columns([2, 1])

with c3:
    fig_reg = px.bar(
        df_region,
        x="REGION", y="REMISE_MOYENNE",
        labels={"REGION": "Région", "REMISE_MOYENNE": "Remise moyenne (%)"},
        color="NB_PROMOTIONS",
        color_continuous_scale=["#FAEEDA", "#633806"],
        text_auto=True
    )
    fig_reg.update_layout(coloraxis_colorbar_title="Nb promos", margin=dict(t=20))
    st.plotly_chart(fig_reg, use_container_width=True)

with c4:
    st.dataframe(
        df_region.rename(columns={
            "REGION": "Région",
            "REMISE_MOYENNE": "Remise moy. (%)",
            "NB_PROMOTIONS": "Nb promotions"
        }),
        use_container_width=True,
        hide_index=True
    )

st.markdown("---")

# ── Top 50 campagnes – tableau complet ──────────────────────────────────────
st.subheader("Tableau complet des performances (Top 50)")

# Filtre interactif
types = ["Tous"] + sorted(df_perf["CAMPAIGN_TYPE"].unique().tolist())
selected = st.selectbox("Filtrer par type de campagne", types)

df_display = df_perf if selected == "Tous" else df_perf[df_perf["CAMPAIGN_TYPE"] == selected]

st.dataframe(
    df_display.rename(columns={
        "CAMPAIGN_NAME": "Campagne",
        "CAMPAIGN_TYPE": "Type",
        "PRODUCT_CATEGORY": "Catégorie",
        "BUDGET": "Budget (€)",
        "ESTIMATIONS_CONVERSIONS": "Conv. estimées",
        "REVENU_ESTIME": "Revenu estimé (€)",
        "RATIO_PERFORMANCE": "Ratio perf."
    }),
    use_container_width=True,
    hide_index=True
)
st.caption("Revenu estimé = Conversions × 15€ (panier moyen fictif). Ratio perf. = Revenu estimé / Budget.")
