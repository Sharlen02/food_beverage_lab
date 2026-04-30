import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Ventes & Promotions", layout="wide")
session = get_active_session()

st.title("📈 Ventes & Promotions")
st.markdown("Analyse du chiffre d'affaires, de l'impact promotionnel et de la sensibilité par catégorie.")

# ── Chargement des données ──────────────────────────────────────────────────

@st.cache_data
def load_promo_split():
    return session.sql("""
        WITH ESTIMATION AS (
            SELECT
                SUM(BUDGET)                          AS TOTAL_BUDGET,
                SUM(REACH * CONVERSION_RATE * 0.1)   AS REVENU_PROMO
            FROM ANYCOMPANY_LAB.SILVER.MARKETING_CAMPAIGNS_CLEAN
        ),
        CA AS (
            SELECT SUM(AMOUNT) AS CA_TOTAL
            FROM ANYCOMPANY_LAB.SILVER.FINANCIAL_TRANSACTIONS_CLEAN
            WHERE TRANSACTION_TYPE = 'Sale'
        )
        SELECT
            'Ventes liées au Marketing / Promo'   AS CATEGORIE,
            ROUND(E.REVENU_PROMO, 2)              AS MONTANT,
            ROUND((E.REVENU_PROMO / C.CA_TOTAL) * 100, 2) AS POURCENTAGE
        FROM ESTIMATION E, CA C
        UNION ALL
        SELECT
            'Ventes Organiques (Sans Promo)',
            ROUND(C.CA_TOTAL - E.REVENU_PROMO, 2),
            ROUND(((C.CA_TOTAL - E.REVENU_PROMO) / C.CA_TOTAL) * 100, 2)
        FROM ESTIMATION E, CA C
    """).to_pandas()

@st.cache_data
def load_ca_total():
    return session.sql("""
        SELECT
            SUM(AMOUNT)   AS CA_TOTAL,
            COUNT(*)      AS NB_TRANSACTIONS,
            ROUND(AVG(AMOUNT), 2) AS PANIER_MOYEN
        FROM ANYCOMPANY_LAB.SILVER.FINANCIAL_TRANSACTIONS_CLEAN
        WHERE TRANSACTION_TYPE = 'Sale'
    """).to_pandas()

@st.cache_data
def load_monthly_sales():
    return session.sql("""
        SELECT
            DATE_TRUNC('MONTH', TRANSACTION_DATE) AS MOIS,
            SUM(AMOUNT)   AS VENTES_MENSUELLES,
            COUNT(*)      AS NB_VENTES
        FROM ANYCOMPANY_LAB.SILVER.FINANCIAL_TRANSACTIONS_CLEAN
        WHERE TRANSACTION_TYPE = 'Sale'
        GROUP BY 1
        ORDER BY 1
    """).to_pandas()

@st.cache_data
def load_cumulative_sales():
    return session.sql("""
        WITH MONTHLY AS (
            SELECT
                DATE_TRUNC('MONTH', TRANSACTION_DATE) AS MOIS,
                SUM(AMOUNT) AS MONTANT_MENSUEL
            FROM ANYCOMPANY_LAB.SILVER.FINANCIAL_TRANSACTIONS_CLEAN
            WHERE TRANSACTION_TYPE = 'Sale'
            GROUP BY 1
        )
        SELECT
            MOIS,
            MONTANT_MENSUEL,
            SUM(MONTANT_MENSUEL) OVER (ORDER BY MOIS) AS CUMUL
        FROM MONTHLY
        ORDER BY MOIS
    """).to_pandas()

@st.cache_data
def load_category_sensitivity():
    return session.sql("""
        SELECT
            PRODUCT_CATEGORY,
            COUNT(PROMOTION_ID)                          AS NB_PROMOTIONS,
            ROUND(AVG(DISCOUNT_PERCENTAGE), 2)           AS REMISE_MOYENNE_PCT,
            ROUND(AVG(DATEDIFF('day', START_DATE, END_DATE)), 1) AS DUREE_MOYENNE_JOURS
        FROM ANYCOMPANY_LAB.SILVER.PROMOTIONS_DATA_CLEAN
        GROUP BY PRODUCT_CATEGORY
        ORDER BY REMISE_MOYENNE_PCT DESC
    """).to_pandas()

@st.cache_data
def load_yearly_sales():
    return session.sql("""
        SELECT
            YEAR(TRANSACTION_DATE) AS ANNEE,
            SUM(AMOUNT)            AS VENTES_ANNUELLES
        FROM ANYCOMPANY_LAB.SILVER.FINANCIAL_TRANSACTIONS_CLEAN
        WHERE TRANSACTION_TYPE = 'Sale'
        GROUP BY 1
        ORDER BY 1
    """).to_pandas()

@st.cache_data
def load_regional_sales():
    return session.sql("""
        SELECT
            REGION,
            SUM(AMOUNT)            AS TOTAL_VENTES,
            COUNT(*)               AS NB_TRANSACTIONS,
            ROUND(AVG(AMOUNT), 2)  AS PANIER_MOYEN
        FROM ANYCOMPANY_LAB.SILVER.FINANCIAL_TRANSACTIONS_CLEAN
        WHERE TRANSACTION_TYPE = 'Sale'
        GROUP BY REGION
        ORDER BY TOTAL_VENTES DESC
    """).to_pandas()

# ── Chargement ──────────────────────────────────────────────────────────────
with st.spinner("Chargement des données..."):
    df_split     = load_promo_split()
    df_ca        = load_ca_total()
    df_monthly   = load_monthly_sales()
    df_cumul     = load_cumulative_sales()
    df_cat       = load_category_sensitivity()
    df_yearly    = load_yearly_sales()
    df_regional  = load_regional_sales()

# ── KPIs ────────────────────────────────────────────────────────────────────
st.subheader("Indicateurs clés")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Chiffre d'affaires total",  f"€{df_ca['CA_TOTAL'][0]:,.0f}")
k2.metric("Nombre de transactions",    f"{df_ca['NB_TRANSACTIONS'][0]:,}")
k3.metric("Panier moyen",              f"€{df_ca['PANIER_MOYEN'][0]:,.2f}")
pct_promo = df_split.loc[df_split['CATEGORIE'].str.contains('Promo'), 'POURCENTAGE'].values
k4.metric("Part ventes promo",         f"{pct_promo[0]:.1f}%" if len(pct_promo) else "N/A")

st.markdown("---")

# ── Split Promo / Organique ──────────────────────────────────────────────────
st.subheader("Répartition : ventes promo vs organiques")
c1, c2 = st.columns([1, 2])

with c1:
    fig_donut = px.pie(
        df_split,
        values="POURCENTAGE",
        names="CATEGORIE",
        hole=0.6,
        color_discrete_sequence=["#1D9E75", "#378ADD"]
    )
    fig_donut.update_traces(textinfo="percent+label")
    fig_donut.update_layout(showlegend=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig_donut, use_container_width=True)

with c2:
    st.dataframe(
        df_split.rename(columns={
            "CATEGORIE": "Catégorie",
            "MONTANT": "Montant (€)",
            "POURCENTAGE": "Part (%)"
        }),
        use_container_width=True,
        hide_index=True
    )
    st.caption("💡 La grande majorité des ventes est organique. Le levier promotionnel reste sous-exploité ou peu mesurable avec les données disponibles.")

st.markdown("---")

# ── Évolution mensuelle ──────────────────────────────────────────────────────
st.subheader("Évolution des ventes dans le temps")
tab1, tab2, tab3 = st.tabs(["Par mois", "Par année", "Cumulées"])

with tab1:
    fig_monthly = px.bar(
        df_monthly,
        x="MOIS", y="VENTES_MENSUELLES",
        labels={"MOIS": "Mois", "VENTES_MENSUELLES": "Ventes (€)"},
        color_discrete_sequence=["#378ADD"]
    )
    fig_monthly.update_layout(margin=dict(t=20))
    st.plotly_chart(fig_monthly, use_container_width=True)

with tab2:
    fig_yearly = px.bar(
        df_yearly,
        x="ANNEE", y="VENTES_ANNUELLES",
        labels={"ANNEE": "Année", "VENTES_ANNUELLES": "Ventes (€)"},
        color_discrete_sequence=["#7F77DD"],
        text_auto=True
    )
    fig_yearly.update_layout(margin=dict(t=20))
    st.plotly_chart(fig_yearly, use_container_width=True)

with tab3:
    fig_cumul = go.Figure()
    fig_cumul.add_trace(go.Scatter(
        x=df_cumul["MOIS"], y=df_cumul["CUMUL"],
        mode="lines+markers", fill="tozeroy",
        line=dict(color="#1D9E75", width=2),
        fillcolor="rgba(29,158,117,0.1)",
        name="Cumul"
    ))
    fig_cumul.add_trace(go.Bar(
        x=df_cumul["MOIS"], y=df_cumul["MONTANT_MENSUEL"],
        name="Mensuel", marker_color="rgba(55,138,221,0.5)"
    ))
    fig_cumul.update_layout(
        yaxis_title="Montant (€)", xaxis_title="Mois",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=40)
    )
    st.plotly_chart(fig_cumul, use_container_width=True)

st.markdown("---")

# ── Sensibilité par catégorie ────────────────────────────────────────────────
st.subheader("Sensibilité aux promotions par catégorie")
c3, c4 = st.columns([2, 1])

with c3:
    fig_cat = px.bar(
        df_cat,
        x="REMISE_MOYENNE_PCT", y="PRODUCT_CATEGORY",
        orientation="h",
        labels={"REMISE_MOYENNE_PCT": "Remise moyenne (%)", "PRODUCT_CATEGORY": "Catégorie"},
        color="REMISE_MOYENNE_PCT",
        color_continuous_scale=["#E6F1FB", "#185FA5"]
    )
    fig_cat.update_layout(coloraxis_showscale=False, margin=dict(t=20))
    st.plotly_chart(fig_cat, use_container_width=True)

with c4:
    st.dataframe(
        df_cat.rename(columns={
            "PRODUCT_CATEGORY": "Catégorie",
            "NB_PROMOTIONS": "Nb promos",
            "REMISE_MOYENNE_PCT": "Remise moy. (%)",
            "DUREE_MOYENNE_JOURS": "Durée moy. (j)"
        }),
        use_container_width=True,
        hide_index=True
    )

st.markdown("---")

# ── Performance régionale ────────────────────────────────────────────────────
st.subheader("Performance par région")
fig_region = px.bar(
    df_regional,
    x="REGION", y="TOTAL_VENTES",
    labels={"REGION": "Région", "TOTAL_VENTES": "Ventes totales (€)"},
    color="TOTAL_VENTES",
    color_continuous_scale=["#E1F5EE", "#0F6E56"],
    text_auto=True
)
fig_region.update_layout(coloraxis_showscale=False, margin=dict(t=20))
st.plotly_chart(fig_region, use_container_width=True)
