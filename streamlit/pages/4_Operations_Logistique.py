import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Opérations & Logistique", layout="wide")
session = get_active_session()

st.title("🚚 Opérations & Logistique")
st.markdown("Surveillance des stocks, alertes de rupture et analyse de l'impact des délais de livraison.")

# ── Chargement des données ──────────────────────────────────────────────────

@st.cache_data
def load_inventory():
    return session.sql("""
        SELECT
            PRODUCT_ID,
            PRODUCT_CATEGORY,
            COUNTRY,
            CURRENT_STOCK,
            CASE
                WHEN CURRENT_STOCK < 500   THEN 'Rupture imminente'
                WHEN CURRENT_STOCK < 1000  THEN 'Stock faible'
                WHEN CURRENT_STOCK < 1500  THEN 'Stock bas'
                WHEN CURRENT_STOCK < 2500  THEN 'Stock correct'
                ELSE                            'Stock optimal'
            END AS STATUT_ALERTE,
            CASE
                WHEN CURRENT_STOCK < 1000 THEN 'À réapprovisionner'
                ELSE 'À surveiller'
            END AS PRIORITE_ACTION
        FROM ANYCOMPANY_LAB.SILVER.INVENTORY_CLEAN
        ORDER BY CURRENT_STOCK ASC
    """).to_pandas()

@st.cache_data
def load_logistics_impact():
    return session.sql("""
        WITH BASE_STATS AS (
            SELECT
                L.DESTINATION_COUNTRY                                        AS PAYS,
                I.PRODUCT_CATEGORY,
                ROUND(AVG(DATEDIFF('day', L.SHIP_DATE, L.ESTIMATED_DELIVERY)), 1) AS DELAI_MOYEN,
                COUNT(L.SHIPMENT_ID)                                         AS VOLUME_COMMANDES,
                ROUND((AVG(DATEDIFF('day', L.SHIP_DATE, L.ESTIMATED_DELIVERY))
                       * COUNT(L.SHIPMENT_ID)) / 100, 2)                     AS SCORE_IMPACT
            FROM ANYCOMPANY_LAB.SILVER.LOGISTICS_AND_SHIPPING_CLEAN L
            INNER JOIN ANYCOMPANY_LAB.SILVER.INVENTORY_CLEAN I
                ON L.DESTINATION_COUNTRY = I.COUNTRY
            WHERE L.ESTIMATED_DELIVERY IS NOT NULL
            GROUP BY 1, 2
            HAVING COUNT(L.SHIPMENT_ID) > 10
        )
        SELECT
            PAYS,
            PRODUCT_CATEGORY,
            DELAI_MOYEN,
            VOLUME_COMMANDES,
            SCORE_IMPACT,
            CASE
                WHEN SCORE_IMPACT > 50 THEN 'CRITIQUE'
                WHEN SCORE_IMPACT > 20 THEN 'ÉLEVÉ'
                WHEN SCORE_IMPACT > 10 THEN 'MODÉRÉ'
                ELSE 'FAIBLE'
            END AS NIVEAU_IMPACT,
            CASE
                WHEN SCORE_IMPACT > 50 THEN 'Changement transporteur ou entrepôt local requis'
                WHEN SCORE_IMPACT > 20 THEN 'Optimisation des routes de livraison'
                WHEN SCORE_IMPACT > 10 THEN 'Surveillance des délais'
                ELSE 'Maintenir les opérations'
            END AS ACTION_RECOMMANDEE
        FROM BASE_STATS
        ORDER BY SCORE_IMPACT DESC
    """).to_pandas()

@st.cache_data
def load_shipping_methods():
    return session.sql("""
        SELECT
            SHIPPING_METHOD,
            STATUS,
            COUNT(*)                                             AS NB_EXPEDITIONS,
            ROUND(AVG(SHIPPING_COST), 2)                        AS COUT_MOYEN,
            ROUND(AVG(DATEDIFF('day', SHIP_DATE, ESTIMATED_DELIVERY)), 1) AS DELAI_MOYEN
        FROM ANYCOMPANY_LAB.SILVER.LOGISTICS_AND_SHIPPING_CLEAN
        WHERE ESTIMATED_DELIVERY IS NOT NULL
        GROUP BY SHIPPING_METHOD, STATUS
        ORDER BY NB_EXPEDITIONS DESC
    """).to_pandas()

# ── Chargement ──────────────────────────────────────────────────────────────
with st.spinner("Chargement des données opérationnelles..."):
    df_inv     = load_inventory()
    df_log     = load_logistics_impact()
    df_ship    = load_shipping_methods()

# ── KPIs ────────────────────────────────────────────────────────────────────
st.subheader("Indicateurs clés")
k1, k2, k3, k4 = st.columns(4)
pct_rupture = (df_inv["STATUT_ALERTE"] == "Rupture imminente").mean() * 100
pct_reap    = (df_inv["PRIORITE_ACTION"] == "À réapprovisionner").mean() * 100
nb_critique = (df_log["NIVEAU_IMPACT"] == "CRITIQUE").sum()
delai_moy   = df_log["DELAI_MOYEN"].mean()

k1.metric("Rupture imminente",      f"{pct_rupture:.0f}% des références", delta=None)
k2.metric("À réapprovisionner",     f"{pct_reap:.0f}% des références")
k3.metric("Délai livraison moyen",  f"{delai_moy:.1f} jours")
k4.metric("Zones impact critique",  f"{nb_critique}")

st.markdown("---")

# ── Alertes stock ────────────────────────────────────────────────────────────
st.subheader("Alertes stock par statut")

statut_order = ["Rupture imminente", "Stock faible", "Stock bas", "Stock correct", "Stock optimal"]
color_map_stock = {
    "Rupture imminente": "#E24B4A",
    "Stock faible":      "#EF9F27",
    "Stock bas":         "#BA7517",
    "Stock correct":     "#1D9E75",
    "Stock optimal":     "#378ADD"
}

df_stock_summary = (
    df_inv.groupby("STATUT_ALERTE")
    .size()
    .reset_index(name="NB_PRODUITS")
)

c1, c2 = st.columns([1, 2])
with c1:
    fig_donut = px.pie(
        df_stock_summary,
        values="NB_PRODUITS", names="STATUT_ALERTE",
        hole=0.55,
        color="STATUT_ALERTE",
        color_discrete_map=color_map_stock,
        category_orders={"STATUT_ALERTE": statut_order}
    )
    fig_donut.update_traces(textinfo="percent+label")
    fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig_donut, use_container_width=True)

with c2:
    # Filtre interactif par statut
    selected_statuts = st.multiselect(
        "Filtrer par statut d'alerte",
        options=statut_order,
        default=["Rupture imminente", "Stock faible"]
    )
    df_filtered = df_inv[df_inv["STATUT_ALERTE"].isin(selected_statuts)] if selected_statuts else df_inv

    st.dataframe(
        df_filtered[["PRODUCT_ID","PRODUCT_CATEGORY","COUNTRY","CURRENT_STOCK","STATUT_ALERTE","PRIORITE_ACTION"]]
        .rename(columns={
            "PRODUCT_ID": "Produit",
            "PRODUCT_CATEGORY": "Catégorie",
            "COUNTRY": "Pays",
            "CURRENT_STOCK": "Stock actuel",
            "STATUT_ALERTE": "Statut",
            "PRIORITE_ACTION": "Action"
        }),
        use_container_width=True,
        hide_index=True,
        height=280
    )

st.markdown("---")

# ── Stock par catégorie ──────────────────────────────────────────────────────
st.subheader("Niveau de stock moyen par catégorie et pays")

df_cat_stock = (
    df_inv.groupby(["PRODUCT_CATEGORY", "COUNTRY"])["CURRENT_STOCK"]
    .mean()
    .reset_index()
    .rename(columns={"CURRENT_STOCK": "STOCK_MOYEN"})
)

fig_box = px.box(
    df_inv,
    x="PRODUCT_CATEGORY", y="CURRENT_STOCK",
    color="STATUT_ALERTE",
    color_discrete_map=color_map_stock,
    labels={"PRODUCT_CATEGORY":"Catégorie","CURRENT_STOCK":"Stock actuel"},
    points="outliers"
)
fig_box.update_layout(margin=dict(t=10))
st.plotly_chart(fig_box, use_container_width=True)

st.markdown("---")

# ── Impact logistique ────────────────────────────────────────────────────────
st.subheader("Impact logistique par pays et catégorie")
st.caption("Score impact = (Délai moyen × Volume commandes) / 100. Plus le score est élevé, plus l'impact est critique.")

color_map_impact = {
    "CRITIQUE": "#E24B4A",
    "ÉLEVÉ":    "#BA7517",
    "MODÉRÉ":   "#378ADD",
    "FAIBLE":   "#1D9E75"
}

# Filtre par niveau d'impact
niveaux = st.multiselect(
    "Filtrer par niveau d'impact",
    options=["CRITIQUE", "ÉLEVÉ", "MODÉRÉ", "FAIBLE"],
    default=["CRITIQUE", "ÉLEVÉ"]
)
df_log_f = df_log[df_log["NIVEAU_IMPACT"].isin(niveaux)] if niveaux else df_log

fig_log = px.scatter(
    df_log_f,
    x="DELAI_MOYEN", y="VOLUME_COMMANDES",
    size="SCORE_IMPACT",
    color="NIVEAU_IMPACT",
    hover_name="PAYS",
    hover_data={"PRODUCT_CATEGORY": True, "ACTION_RECOMMANDEE": True},
    labels={
        "DELAI_MOYEN": "Délai moyen (jours)",
        "VOLUME_COMMANDES": "Volume de commandes",
        "NIVEAU_IMPACT": "Niveau"
    },
    color_discrete_map=color_map_impact
)
fig_log.update_layout(margin=dict(t=10))
st.plotly_chart(fig_log, use_container_width=True)

with st.expander("Voir le tableau détaillé des impacts logistiques"):
    st.dataframe(
        df_log_f.rename(columns={
            "PAYS": "Pays",
            "PRODUCT_CATEGORY": "Catégorie",
            "DELAI_MOYEN": "Délai moy. (j)",
            "VOLUME_COMMANDES": "Volume",
            "SCORE_IMPACT": "Score impact",
            "NIVEAU_IMPACT": "Niveau",
            "ACTION_RECOMMANDEE": "Action recommandée"
        }),
        use_container_width=True,
        hide_index=True
    )

st.markdown("---")

# ── Méthodes d'expédition ────────────────────────────────────────────────────
st.subheader("Méthodes d'expédition : coût et délai")
c3, c4 = st.columns(2)

df_ship_agg = (
    df_ship.groupby("SHIPPING_METHOD")
    .agg(COUT_MOYEN=("COUT_MOYEN", "mean"), DELAI_MOYEN=("DELAI_MOYEN", "mean"), NB=("NB_EXPEDITIONS", "sum"))
    .reset_index()
)

with c3:
    fig_cout = px.bar(
        df_ship_agg,
        x="SHIPPING_METHOD", y="COUT_MOYEN",
        labels={"SHIPPING_METHOD": "Méthode", "COUT_MOYEN": "Coût moyen (€)"},
        color="COUT_MOYEN",
        color_continuous_scale=["#FAEEDA","#412402"],
        text_auto=True
    )
    fig_cout.update_layout(coloraxis_showscale=False, title="Coût moyen par méthode", margin=dict(t=40))
    st.plotly_chart(fig_cout, use_container_width=True)

with c4:
    fig_delai = px.bar(
        df_ship_agg,
        x="SHIPPING_METHOD", y="DELAI_MOYEN",
        labels={"SHIPPING_METHOD": "Méthode", "DELAI_MOYEN": "Délai moyen (j)"},
        color="DELAI_MOYEN",
        color_continuous_scale=["#E1F5EE","#04342C"],
        text_auto=True
    )
    fig_delai.update_layout(coloraxis_showscale=False, title="Délai moyen par méthode", margin=dict(t=40))
    st.plotly_chart(fig_delai, use_container_width=True)
