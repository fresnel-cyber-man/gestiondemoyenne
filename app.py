# app.py
import streamlit as st
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Numeric,
    ForeignKey,
    select,
    inspect,
    text,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
import pandas as pd
from dotenv import load_dotenv
import os
from fpdf import FPDF

load_dotenv()  # charge .env
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    st.error(
        "Pas de DATABASE_URL défini. Duplique .env.example en .env et configure DATABASE_URL."
    )
    st.stop()

# DB setup
engine = create_engine(DATABASE_URL, echo=False, future=True)
metadata = MetaData()

classes = Table(
    "classes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nom", String(100), nullable=False, unique=True),
)

eleves = Table(
    "eleves",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nom", String(100), nullable=False),
    Column("prenom", String(100), nullable=False),
    Column("matricule", String(50), nullable=False, unique=True),
    Column(
        "classe_id",
        Integer,
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    ),
)

matieres = Table(
    "matieres",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("nom", String(100), nullable=False),
    Column("coefficient", Integer, nullable=False),
    Column(
        "classe_id",
        Integer,
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    ),
)

notes = Table(
    "notes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "eleve_id", Integer, ForeignKey("eleves.id", ondelete="CASCADE"), nullable=False
    ),
    Column(
        "matiere_id",
        Integer,
        ForeignKey("matieres.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("note", Numeric(4, 2), nullable=False),
)

# Création si nécessaire (si tu n'as pas exécuté db_init.sql)
metadata.create_all(engine)

Session = sessionmaker(bind=engine)


# ---------- Utils ----------
def load_table_df(table):
    with engine.connect() as conn:
        df = pd.read_sql(select(table), conn)
    return df


def moyenne_par_eleve(eleve_id):
    with engine.connect() as conn:
        q = text("""
        SELECT SUM(n.note * m.coefficient)::numeric / SUM(m.coefficient) AS moyenne
        FROM notes n JOIN matieres m ON n.matiere_id = m.id
        WHERE n.eleve_id = :eid
        """)
        res = conn.execute(q, {"eid": eleve_id}).scalar()
        return float(res) if res is not None else None


def generate_bulletin_pdf(eleve_id):
    # Récupération données
    with engine.connect() as conn:
        eleve = (
            conn.execute(select(eleves).where(eleves.c.id == eleve_id))
            .mappings()
            .first()
        )
        rows = (
            conn.execute(
                text("""
            SELECT m.nom as matiere, m.coefficient, n.note
            FROM notes n JOIN matieres m ON n.matiere_id = m.id
            WHERE n.eleve_id = :eid
            """),
                {"eid": eleve_id},
            )
            .mappings()
            .all()
        )
        moy = moyenne_par_eleve(eleve_id)

    # Génération PDF simple
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, txt="Bulletin de notes", ln=1, align="C")
    pdf.ln(4)
    pdf.cell(0, 6, txt=f"Nom: {eleve['nom']} {eleve['prenom']}", ln=1)
    pdf.cell(0, 6, txt=f"Matricule: {eleve['matricule']}", ln=1)
    pdf.cell(0, 6, txt="", ln=1)
    # Table
    pdf.set_font("Arial", size=11)
    pdf.cell(80, 7, "Matiere", border=1)
    pdf.cell(30, 7, "Coeff.", border=1, align="C")
    pdf.cell(30, 7, "Note", border=1, align="C")
    pdf.ln()
    for r in rows:
        pdf.cell(80, 7, str(r["matiere"]), border=1)
        pdf.cell(30, 7, str(r["coefficient"]), border=1, align="C")
        pdf.cell(30, 7, str(float(r["note"])), border=1, align="C")
        pdf.ln()
    pdf.ln(4)
    pdf.cell(
        0,
        7,
        txt=f"Moyenne générale: {round(moy, 2) if moy is not None else 'N/A'}",
        ln=1,
    )
    # Retour bytes
    return bytes(pdf.output())


# ---------- Streamlit UI ----------
st.set_page_config(page_title="SI Moyennes - Streamlit", layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Aller à",
    ["Accueil", "Classes", "Élèves", "Matières", "Notes", "Bulletins", "Admin DB"],
)

st.title("Système de gestion des moyennes (version simplifiée)")

if page == "Accueil":
    # Stats
    c = load_table_df(classes)
    e = load_table_df(eleves)
    m = load_table_df(matieres)
    n = load_table_df(notes)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Classes", len(c))
    col2.metric("Élèves", len(e))
    col3.metric("Matières", len(m))
    col4.metric("Notes", len(n))
    st.markdown("#### Derniers 10 notes")
    if len(n) > 0:
        st.dataframe(n.sort_values("id", ascending=False).head(10))
    else:
        st.info("Aucune note enregistrée")

elif page == "Classes":
    st.header("Gestion des classes")
    with st.form("form_add_classe"):
        nom = st.text_input("Nom de la classe")
        submitted = st.form_submit_button("Ajouter")
        if submitted:
            if not nom.strip():
                st.error("Nom vide")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(classes.insert().values(nom=nom.strip()))
                    st.success("Classe ajoutée")
                except IntegrityError:
                    st.error("Classe déjà existante")
    df = load_table_df(classes)
    st.dataframe(df)

elif page == "Élèves":
    st.header("Gestion des élèves")
    df_classes = load_table_df(classes)
    if df_classes.empty:
        st.warning("Ajoute d'abord des classes")
    else:
        with st.form("form_add_eleve"):
            nom = st.text_input("Nom")
            prenom = st.text_input("Prénom")
            matricule = st.text_input("Matricule")
            classe_choice = st.selectbox(
                "Classe", df_classes["id"].astype(str) + " - " + df_classes["nom"]
            )
            submitted = st.form_submit_button("Ajouter")
            if submitted:
                try:
                    classe_id = int(classe_choice.split(" - ")[0])
                    with engine.begin() as conn:
                        conn.execute(
                            eleves.insert().values(
                                nom=nom.strip(),
                                prenom=prenom.strip(),
                                matricule=matricule.strip(),
                                classe_id=classe_id,
                            )
                        )
                    st.success("Élève ajouté")
                except IntegrityError:
                    st.error("Matricule déjà existant ou donnée invalide")
        st.markdown("### Liste des élèves")
        df = load_table_df(eleves)
        st.dataframe(df)

elif page == "Matières":
    st.header("Gestion des matières")
    df_classes = load_table_df(classes)
    if df_classes.empty:
        st.warning("Ajoute d'abord des classes")
    else:
        with st.form("form_add_matiere"):
            nom = st.text_input("Nom de la matière")
            coeff = st.number_input("Coefficient", min_value=1, value=1)
            classe_choice = st.selectbox(
                "Classe", df_classes["id"].astype(str) + " - " + df_classes["nom"]
            )
            submitted = st.form_submit_button("Ajouter")
            if submitted:
                try:
                    classe_id = int(classe_choice.split(" - ")[0])
                    with engine.begin() as conn:
                        conn.execute(
                            matieres.insert().values(
                                nom=nom.strip(),
                                coefficient=int(coeff),
                                classe_id=classe_id,
                            )
                        )
                    st.success("Matière ajoutée")
                except IntegrityError:
                    st.error("Cette matière existe déjà pour la classe")
        st.markdown("### Liste des matières")
        df = pd.read_sql(select(matieres).order_by(matieres.c.classe_id), engine)
        st.dataframe(df)

elif page == "Notes":
    st.header("Gestion des notes")
    df_classes = load_table_df(classes)
    if df_classes.empty:
        st.warning("Ajoute d'abord des classes")
    else:
        classe_choice = st.selectbox(
            "Sélectionner une classe pour saisir des notes",
            df_classes["id"].astype(str) + " - " + df_classes["nom"],
        )
        classe_id = int(classe_choice.split(" - ")[0])
        df_eleves = pd.read_sql(
            select(eleves).where(eleves.c.classe_id == classe_id), engine
        )
        df_matieres = pd.read_sql(
            select(matieres).where(matieres.c.classe_id == classe_id), engine
        )
        st.markdown("### Saisie manuelle")
        if df_eleves.empty or df_matieres.empty:
            st.info("Il faut au moins un élève et une matière dans la classe")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                eleve_choice = st.selectbox(
                    "Élève",
                    df_eleves["id"].astype(str)
                    + " - "
                    + df_eleves["prenom"]
                    + " "
                    + df_eleves["nom"],
                )
            with col2:
                mat_choice = st.selectbox(
                    "Matière",
                    df_matieres["id"].astype(str) + " - " + df_matieres["nom"],
                )
            with col3:
                note_val = st.number_input(
                    "Note (0-20)", min_value=0.0, max_value=20.0, value=10.0, step=0.25
                )
            if st.button("Ajouter / Mettre à jour la note"):
                eid = int(eleve_choice.split(" - ")[0])
                mid = int(mat_choice.split(" - ")[0])
                # insert or update (unique eleve_id, matiere_id)
                with engine.begin() as conn:
                    # delete existing if present
                    conn.execute(
                        text(
                            "DELETE FROM notes WHERE eleve_id = :eid AND matiere_id = :mid"
                        ),
                        {"eid": eid, "mid": mid},
                    )
                    conn.execute(
                        notes.insert().values(
                            eleve_id=eid, matiere_id=mid, note=note_val
                        )
                    )
                st.success("Note enregistrée")
        st.markdown("### Tableau des notes (classe sélectionnée)")
        df_notes = pd.read_sql(
            text("""
            SELECT n.id, e.matricule, e.nom as nom_eleve, e.prenom, m.nom as matiere, m.coefficient, n.note
            FROM notes n
            JOIN eleves e ON n.eleve_id = e.id
            JOIN matieres m ON n.matiere_id = m.id
            WHERE e.classe_id = :cid
            ORDER BY e.nom, m.nom
        """),
            engine,
            params={"cid": classe_id},
        )
        st.dataframe(df_notes)

elif page == "Bulletins":
    st.header("Bulletins")
    df_classes = load_table_df(classes)
    if df_classes.empty:
        st.warning("Ajoute d'abord des classes")
    else:
        classe_choice = st.selectbox(
            "Classe", df_classes["id"].astype(str) + " - " + df_classes["nom"]
        )
        classe_id = int(classe_choice.split(" - ")[0])
        df_eleves = pd.read_sql(
            select(eleves).where(eleves.c.classe_id == classe_id), engine
        )
        if df_eleves.empty:
            st.info("Pas d'élève dans la classe")
        else:
            eleve_choice = st.selectbox(
                "Élève",
                df_eleves["id"].astype(str)
                + " - "
                + df_eleves["prenom"]
                + " "
                + df_eleves["nom"],
            )
            eleve_id = int(eleve_choice.split(" - ")[0])
            if st.button("Générer PDF du bulletin"):
                pdf_bytes = generate_bulletin_pdf(eleve_id)
                st.download_button(
                    "Télécharger le bulletin (PDF)",
                    data=pdf_bytes,
                    file_name=f"bulletin_{eleve_id}.pdf",
                    mime="application/pdf",
                )
            # Affichage sur la page
            st.markdown("### Aperçu (tableau)")
            df_b = pd.read_sql(
                text("""
                SELECT m.nom as matiere, m.coefficient, n.note
                FROM notes n JOIN matieres m ON n.matiere_id = m.id
                WHERE n.eleve_id = :eid
            """),
                engine,
                params={"eid": eleve_id},
            )
            st.dataframe(df_b)
            moy = moyenne_par_eleve(eleve_id)
            st.markdown(
                f"**Moyenne générale:** {round(moy, 2) if moy is not None else 'N/A'}"
            )

elif page == "Admin DB":
    st.header("Admin DB")
    if st.button("Exécuter le script d'initialisation (db_init.sql)"):
        # Cherche fichier db_init.sql à la racine
        if not os.path.exists("db_init.sql"):
            st.error("Place db_init.sql à la racine du projet.")
        else:
            sql = open("db_init.sql", "r", encoding="utf-8").read()
            with engine.begin() as conn:
                conn.execute(text(sql))
            st.success("Script exécuté. Données initialisées.")
    if st.checkbox("Afficher structure tables"):
        insp = inspect(engine)
        for t in insp.get_table_names():
            st.write("Table:", t)
            cols = insp.get_columns(t)
            st.table(pd.DataFrame(cols))
