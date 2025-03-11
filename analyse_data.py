import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

def run_analysis(df):
    class CrispDMAnalysis:
        def __init__(self, data):
            self.df = data
            
        # ...existing code from CrispDMAnalysis class...
        # (all methods remain the same, just remove file handling parts)

    st.title("Analyse CRISP-DM des données")

    if df is not None:
        st.write("### Aperçu des données")
        st.dataframe(df.head())

        # Lancement de l'analyse
        analysis = CrispDMAnalysis(df)
        
        with st.spinner("Préparation des données..."):
            analysis.data_preparation()
        
        with st.spinner("Modélisation en cours..."):
            analysis.modeling()
        
        # Affichage des résultats
        st.write("### Visualisation des résultats")
        
        # Plot 3D des clusters
        fig = plt.figure(figsize=(20, 5))
        
        # Premier subplot: Vue 3D des clusters
        ax = fig.add_subplot(131, projection='3d')
        scatter = ax.scatter(analysis.X_pca[:, 0], analysis.X_pca[:, 1], analysis.X_pca[:, 2],
                           c=analysis.clusters, cmap='viridis')
        ax.set_title('Segmentation 3D (ACP + K-means)')
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_zlabel('PC3')
        plt.colorbar(scatter, ax=ax, label='Clusters')
        
        # Deuxième subplot: Vue 3D des anomalies
        ax = fig.add_subplot(132, projection='3d')
        scatter = ax.scatter(analysis.X_pca[:, 0], analysis.X_pca[:, 1], analysis.X_pca[:, 2],
                           c=analysis.anomalies, cmap='RdYlBu')
        ax.set_title('Détection d\'anomalies 3D')
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_zlabel('PC3')
        plt.colorbar(scatter, ax=ax, label='Anomalies')
        
        # Troisième subplot: Variance expliquée
        ax = fig.add_subplot(133)
        components = range(1, len(analysis.pca.explained_variance_ratio_) + 1)
        plt.bar(components, analysis.pca.explained_variance_ratio_)
        plt.title('Variance expliquée par composante')
        plt.xlabel('Composante')
        plt.ylabel('Ratio de variance expliquée')
        for i, v in enumerate(analysis.pca.explained_variance_ratio_):
            plt.text(i + 1, v, f'{v:.1%}', ha='center', va='bottom')
        
        st.pyplot(fig)
        
        # Affichage des métriques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nombre de clusters", len(np.unique(analysis.clusters)))
        with col2:
            st.metric("Proportion d'anomalies", f"{(analysis.anomalies == -1).mean():.2%}")
        with col3:
            st.metric("Variance totale expliquée", f"{sum(analysis.pca.explained_variance_ratio_):.2%}")
        
        # Export des résultats
        results = analysis.export_results()
        
        # Bouton de téléchargement
        st.download_button(
            label="📥 Télécharger les résultats",
            data=results.to_csv(index=False).encode('utf-8'),
            file_name='resultats_analyse.csv',
            mime='text/csv'
        )

if __name__ == "__main__":
    st.set_page_config(page_title="Analyse CRISP-DM", layout="wide")
    if 'df' in st.session_state:
        run_analysis(st.session_state.df)
    else:
        st.error("Veuillez d'abord charger des données dans la page principale.")
