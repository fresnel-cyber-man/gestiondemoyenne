# Système de Gestion des Moyennes - Streamlit

Application Streamlit pour gérer les classes, élèves, matières, notes et générer des bulletins PDF.

## Installation

1. Créer un environnement virtuel (recommandé) :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate sur Windows
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurer la base de données :
```bash
cp .env.example .env
# Éditer .env avec vos identifiants PostgreSQL
```
http://localhost:8501
4. Créer la base et initialiser les données :
```bash
createdb gestion_moyennes
psql -U postgres -d gestion_moyennes -f db_init.sql
```

5. Lancer l'application :
```bash
streamlit run app.py
```

## Pages disponibles

- **Accueil** : Statistiques générales
- **Classes** : Gestion des classes
- **Élèves** : Gestion des élèves
- **Matières** : Gestion des matières par classe
- **Notes** : Saisie et consultation des notes
- **Bulletins** : Génération de bulletins PDF
- **Admin DB** : Réinitialisation des données
