# food_beverage_lab
Devoir final d'architecture data.

## 👤 Auteur

Projet réalisé par D'ALMEIDA Morènikè Sharlen, Bientakonne KARAMBIRI, Stephen AGGEY.


***

# 🥤 Food & Beverage Lab – Data Analytics & ML

## 📌 Présentation du projet

**Food & Beverage Lab** est un projet de data analytics et de machine learning construit autour d’un cas d’usage métier réaliste :  
un fabricant de produits alimentaires et de boissons (AnyCompany) confronté à une **baisse significative des ventes** et à une **réduction de 30 % du budget marketing**.

L’objectif est de mettre en place une **chaîne data complète** :

*   ingestion et nettoyage des données (Snowflake),
*   analyses exploratoires,
*   features analytiques et ML,
*   restitution via un **tableau de bord Streamlit interactif**.

***

## 🎯 Objectifs

*   Centraliser et structurer des données hétérogènes (CSV, JSON)
*   Nettoyer et fiabiliser les données (couche **Silver**)
*   Réaliser des analyses métier : ventes, marketing, expérience client, logistique
*   Préparer les variables pour des usages Machine Learning
*   Fournir un **data product** exploitable par les équipes métier

***

## 🗂️ Structure du projet

```text
food_beverage_lab/
│
├── ml/
│   └── phase3_ML.ipynb
│
├── notebooks/
│   ├── phase2-1_Exploration.ipynb
│   ├── phase2-2.ipynb
│   └── phase2-3.ipynb
│
├── sql/
│   ├── load_data.sql
│   └── clean_data.sql
│
├── streamlit/
│   ├── streamlit_app.py
│   └── pages/
│       ├── 1_Ventes_Promos.py
│       ├── 2_Marketing.py
│       ├── 3_Experience_Client.py
│       ├── 4_Operations_Logistique.py
│       └── 5_Features_ML.py
│
└── README.md


***

## 🧱 Architecture Data

### 1️⃣ Couche Bronze – Ingestion des données

*   Chargement depuis un **bucket S3** (CSV et JSON)
*   Création des tables brutes dans Snowflake
*   Script principal :  
    📄 `sql/load_data.sql`

> Inclut la gestion d’un **problème réel de CSV corrompu** (`product_reviews`) avec une stratégie de chargement brut puis parsing contrôlé.

***

### 2️⃣ Couche Silver – Nettoyage & standardisation

*   Suppression des doublons
*   Normalisation des chaînes (`TRIM`, `LOWER`)
*   Conversion des types (dates, nombres)
*   Validation des règles métiers (dates incohérentes, régions invalides, etc.)

📄 Script : `sql/clean_data.sql`  
➡️ Résultat : tables propres prêtes pour l’analyse et le ML

***

## 📊 Analyses & Notebooks

Les notebooks Jupyter permettent une montée progressive en complexité :

*   **Phase 2.1 – Exploration**
    *   Compréhension des données
    *   Statistiques descriptives
    *   Détection d’anomalies

*   **Phase 2.2 & 2.3**
    *   Analyses croisées
    *   Visualisations avancées
    *   Premiers insights métier

📂 Dossier : `notebooks/`

***

## 🤖 Machine Learning

📄 `ml/phase3_ML.ipynb`

*   Analyse des features disponibles
*   Préparation des variables (numériques, catégorielles)
*   Vision analytique orientée **scoring / prédiction**
*   Support à l’industrialisation ML

***

## 🖥️ Application Streamlit – Data Product

L’application Streamlit constitue la **couche de restitution finale**.

### Lancement de l’application

```bash
streamlit run streamlit/streamlit_app.py
```

### Pages disponibles

*   **📈 Ventes & Promotions**  
    Analyse des ventes promotionnelles vs organiques

*   **📣 Marketing**  
    Performance des campagnes, budget, ROI

*   **⭐ Expérience Client**  
    Avis produits, satisfaction, interactions SAV

*   **🚚 Opérations & Logistique**  
    Stocks, délais, alertes logistiques


***

## 🛠️ Technologies utilisées

*   **Snowflake** : stockage & transformation des données
*   **SQL** : ingestion et nettoyage
*   **Python** : analyse, ML, visualisation
*   **Pandas / NumPy / Matplotlib**
*   **Streamlit** : data app interactive
*   **Jupyter Notebook**

***

## ✅ Points forts du projet

*   Cas d’usage métier réaliste
*   Architecture data claire (Bronze / Silver / Analytics)
*   Gestion robuste des erreurs de données
*   Vision end-to-end : Data Engineering → Analytics → ML → Data Product
*   Application Streamlit orientée décisionnel

***