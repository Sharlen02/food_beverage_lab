import streamlit as st

st.set_page_config(
    page_title="AnyCompany - Analytics",
    page_icon="🥤",
    layout="wide"
)

st.title("🥤 AnyCompany Food & Beverage")
st.subheader("Tableau de bord analytique : Data Product")

st.markdown("""
---
### Contexte
AnyCompany est un fabricant de produits alimentaires et de boissons présent depuis plus de 25 ans.
Face à une **baisse des ventes sans précédent** et une réduction de **30 % du budget marketing**,
cette plateforme analytique permet de piloter la reprise par la donnée.

---
### Navigation
Utilisez le menu de gauche pour accéder aux analyses :
""")

col1, col2 = st.columns(2)

with col1:
    st.info("**📈 Ventes & Promotions**\nSplit promo/organique, sensibilité par catégorie, évolution mensuelle et cumulée.")
    st.info("**📣 Marketing**\nPerformance des campagnes, ROI, efficacité par type et région.")
    st.info("**⭐ Expérience Client**\nNotes produits, satisfaction SAV, segmentation démographique.")

with col2:
    st.info("**🚚 Opérations & Logistique**\nAlertes stock, délais de livraison, score d'impact logistique.")
    st.info("**🤖 Features ML**\nArchitecture ANALYTICS, variables ML, distributions clés.")



st.markdown("---")