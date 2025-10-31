import streamlit as st
import pandas as pd
from typing import Optional, List


def load_csv(file, show_error: bool = True) -> Optional[pd.DataFrame]:
    """
    Lit un fichier CSV depuis un UploadedFile de Streamlit (ou tout file-like).

    Arguments:
        file: streamlit.uploaded_file_manager.UploadedFile ou objet file-like
        show_error: si True et si Streamlit est disponible, affiche les erreurs via st.error

    Retour:
        pandas.DataFrame ou None si une erreur est survenue
    """
    if file is None:
        if show_error:
            try:
                st.error("Aucun fichier fourni.")
            except Exception:
                pass
        return None

    # Assurer que le pointeur est au début
    try:
        file.seek(0)
    except Exception:
        # Certains objets UploadedFile n'ont pas seek; ignorer si impossible
        pass

    try:
        # Lecture de base avec pandas (détecte séparateur automatiquement si possible)
        df = pd.read_csv(file)
        return df

    except pd.errors.EmptyDataError:
        if show_error:
            try:
                st.error("Le fichier CSV est vide.")
            except Exception:
                pass
        return None

    except UnicodeDecodeError:
        # Tentative avec un encodage plus permissif
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding="latin-1")
            return df
        except Exception:
            if show_error:
                try:
                    st.error("Erreur d'encodage du fichier CSV. Essayez un encodage différent (ex: UTF-8 / latin-1).")
                except Exception:
                    pass
            return None

    except pd.errors.ParserError:
        if show_error:
            try:
                st.error("Erreur lors de l'analyse du CSV (format invalide).")
            except Exception:
                pass
        return None

    except Exception as e:
        if show_error:
            try:
                st.error(f"Impossible de lire le fichier CSV: {e}")
            except Exception:
                pass
        return None


def list_numeric_columns(df: pd.DataFrame) -> List[str]:
    """
    Retourne la liste des colonnes numériques d'un DataFrame pandas.

    Args:
        df: pandas.DataFrame

    Returns:
        Liste des noms de colonnes (List[str]). Si df est None ou vide, renvoie []
    """
    if df is None:
        return []

    # Utiliser select_dtypes qui est rapide et fiable
    try:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        return numeric_cols
    except Exception:
        # fallback: vérifier chaque colonne
        try:
            from pandas.api.types import is_numeric_dtype
            return [col for col in df.columns if is_numeric_dtype(df[col])]
        except Exception:
            return []


def main() -> None:
    """Streamlit app: upload CSV, show table, select numeric column and plot."""
    st.set_page_config(page_title="CSV Explorer", layout="wide")
    st.title("CSV Explorer — Upload, aperçu et graphique")

    st.sidebar.header("Options")
    show_head = st.sidebar.checkbox("Afficher les premières lignes (head)", value=True)
    max_rows = st.sidebar.number_input("Nombre de lignes à afficher", min_value=5, max_value=1000, value=50, step=5)

    uploaded_file = st.file_uploader("Charger un fichier CSV", type=["csv"], help="Sélectionnez un fichier CSV à visualiser")

    if uploaded_file is None:
        st.info("Uploadez un fichier CSV depuis la barre latérale ou ici pour commencer.")
        # provide a small sample button
        if st.button("Générer un CSV d'exemple"):
            sample_df = pd.DataFrame({
                "x": range(1, 21),
                "y": [v * 2 + (v % 3) for v in range(1, 21)],
                "category": ["A" if v % 2 == 0 else "B" for v in range(1, 21)]
            })
            st.write("CSV d'exemple")
            st.dataframe(sample_df)
            st.download_button("Télécharger l'exemple", data=sample_df.to_csv(index=False), file_name="sample.csv", mime="text/csv")
        return

    # Charger le CSV
    df = load_csv(uploaded_file, show_error=True)
    if df is None:
        return

    # Affichage du DataFrame
    st.subheader("Aperçu du jeu de données")
    with st.expander("Afficher le DataFrame / informations" , expanded=True):
        st.write(f"Dimensions: {df.shape[0]} lignes × {df.shape[1]} colonnes")
        if show_head:
            st.dataframe(df.head(int(max_rows)))
        if st.checkbox("Afficher les statistiques descriptives", value=False):
            st.write(df.describe(include='all'))

    # Liste des colonnes numériques
    numeric_cols = list_numeric_columns(df)
    st.sidebar.subheader("Graphique")
    if not numeric_cols:
        st.sidebar.info("Aucune colonne numérique détectée dans le CSV.")
        st.warning("Aucune colonne numérique trouvée — impossible de tracer un graphique. Vérifiez votre fichier.")
        return

    selected_col = st.sidebar.selectbox("Choisir une colonne numérique", numeric_cols)
    chart_type = st.sidebar.selectbox("Type de graphique", ["Line (série)", "Bar", "Histogramme"])

    st.sidebar.markdown("---")
    agg_option = st.sidebar.checkbox("Afficher résumé (moyenne, médiane)", value=False)

    # Préparer les données de la colonne
    col_series = pd.to_numeric(df[selected_col], errors='coerce')

    st.subheader(f"Visualisation — {selected_col}")

    if agg_option:
        mean_v = col_series.mean()
        median_v = col_series.median()
        st.write(f"Moyenne: {mean_v:.4g}, Médiane: {median_v:.4g}")

    # Choix du graphique
    if chart_type == "Line (série)":
        # st.line_chart gère les index
        st.line_chart(col_series.dropna())
    elif chart_type == "Bar":
        # afficher les premières N valeurs en barre
        st.bar_chart(col_series.dropna().head(100))
    elif chart_type == "Histogramme":
        hist_bins = st.sidebar.slider("Nombre de bins", min_value=5, max_value=200, value=30)
        fig = None
        try:
            import altair as alt
            hist_df = pd.DataFrame({selected_col: col_series.dropna()})
            fig = alt.Chart(hist_df).mark_bar().encode(
                alt.X(f"{selected_col}", bin=alt.Bin(maxbins=hist_bins)),
                y='count()'
            ).properties(height=300)
            st.altair_chart(fig, use_container_width=True)
        except Exception:
            # fallback: utiliser pandas plot (matplotlib)
            try:
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots()
                ax.hist(col_series.dropna(), bins=hist_bins)
                ax.set_xlabel(selected_col)
                ax.set_ylabel('count')
                st.pyplot(fig)
            except Exception as e:
                st.error(f"Impossible de tracer l'histogramme: {e}")

    st.markdown("---")
    st.write("Vous pouvez télécharger les données affichées (CSV) :")
    st.download_button("Télécharger le CSV", data=df.to_csv(index=False), file_name="data.csv", mime="text/csv")


if __name__ == "__main__":
    main()
