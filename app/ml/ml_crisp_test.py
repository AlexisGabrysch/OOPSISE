import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

# 1. Importation des données

data = "C:/Users/aoruezabal/Documents/GitHub/OOPSISE/app/data/iptables.parquet"

df = pd.read_parquet(data)

class CrispDMAnalysis:
    def __init__(self, data_path):
        self.df = pd.read_parquet(data_path)
        
        # Afficher les informations sur les colonnes pour le debug
        print("\nColonnes disponibles:")
        print(self.df.columns.tolist())
        print("\nAperçu des données:")
        print(self.df.head())
        
    def data_preparation(self):
        # Conversion des colonnes en types appropriés
        numeric_features = []
        
        # Conversion des colonnes numériques
        for col in self.df.columns:
            try:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                if not self.df[col].isna().all():  # Vérifie si la colonne contient des données valides
                    numeric_features.append(col)
            except (ValueError, TypeError):
                continue
        
        print("\nColonnes numériques utilisées:", numeric_features)
        
        # Sélection des variables numériques
        X = self.df[numeric_features]
        
        # Imputation des valeurs manquantes
        imputer = SimpleImputer(strategy='mean')
        self.X_imputed = imputer.fit_transform(X)
        
        # Standardisation
        scaler = StandardScaler()
        self.X_scaled = scaler.fit_transform(self.X_imputed)
        
        # Sauvegarde des noms de colonnes
        self.feature_names = numeric_features
        
        return self.X_scaled
        
    def modeling(self):
        # ACP pour la réduction de dimension
        self.pca = PCA(n_components=3)  # Modifié de 2 à 3
        self.X_pca = self.pca.fit_transform(self.X_scaled)
        
        # K-means pour la segmentation
        self.kmeans = KMeans(n_clusters=3, random_state=42)
        self.clusters = self.kmeans.fit_predict(self.X_scaled)
        
        # Isolation Forest pour la détection d'anomalies
        self.iforest = IsolationForest(random_state=42)
        self.anomalies = self.iforest.fit_predict(self.X_scaled)
        
    def evaluation(self):
        self._plot_results()
        self._interpret_results()
        
    def _plot_distributions(self):
        numeric_cols = self.df.select_dtypes(include=['float64', 'int64']).columns
        plt.figure(figsize=(15, 5))
        for i, col in enumerate(numeric_cols[:3], 1):
            plt.subplot(1, 3, i)
            sns.histplot(self.df[col], kde=True)
            plt.title(f'Distribution de {col}')
        plt.tight_layout()
        plt.show()
        
    def _plot_results(self):
        """Visualisation des résultats avec graphique 3D"""
        # Plot 3D des clusters
        fig = plt.figure(figsize=(20, 5))
        
        # Premier subplot: Vue 3D des clusters
        ax = fig.add_subplot(131, projection='3d')
        scatter = ax.scatter(self.X_pca[:, 0], self.X_pca[:, 1], self.X_pca[:, 2],
                           c=self.clusters, cmap='viridis')
        ax.set_title('Segmentation 3D (ACP + K-means)')
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_zlabel('PC3')
        plt.colorbar(scatter, ax=ax, label='Clusters')
        
        # Deuxième subplot: Vue 3D des anomalies
        ax = fig.add_subplot(132, projection='3d')
        scatter = ax.scatter(self.X_pca[:, 0], self.X_pca[:, 1], self.X_pca[:, 2],
                           c=self.anomalies, cmap='RdYlBu')
        ax.set_title('Détection d\'anomalies 3D')
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.set_zlabel('PC3')
        plt.colorbar(scatter, ax=ax, label='Anomalies')
        
        # Troisième subplot: Variance expliquée
        ax = fig.add_subplot(133)
        components = range(1, len(self.pca.explained_variance_ratio_) + 1)
        plt.bar(components, self.pca.explained_variance_ratio_)
        plt.title('Variance expliquée par composante')
        plt.xlabel('Composante')
        plt.ylabel('Ratio de variance expliquée')
        for i, v in enumerate(self.pca.explained_variance_ratio_):
            plt.text(i + 1, v, f'{v:.1%}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.show()
        
    def _interpret_results(self):
        """Interprétation des résultats"""
        print("\nRésultats de l'analyse:")
        print(f"Nombre de clusters identifiés: {len(np.unique(self.clusters))}")
        print(f"Proportion d'anomalies: {(self.anomalies == -1).mean():.2%}")
        print("\nVariance expliquée par l'ACP:")
        print(f"Première composante: {self.pca.explained_variance_ratio_[0]:.2%}")
        print(f"Deuxième composante: {self.pca.explained_variance_ratio_[1]:.2%}")
        print(f"Troisième composante: {self.pca.explained_variance_ratio_[2]:.2%}")
        print(f"Variance totale expliquée: {sum(self.pca.explained_variance_ratio_):.2%}")

    def export_results(self):
        """Export des résultats vers Excel"""
        # Création d'une copie du DataFrame original
        results_df = df.copy()
        
        # Ajout des colonnes pour les clusters et anomalies
        results_df['Cluster'] = self.clusters
        # Conversion des -1 en 0 et 1 en 1 pour les anomalies
        results_df['Est_Anomalie'] = (self.anomalies == -1).astype(int)
        
        # Ajout des composantes principales
        results_df['PC1'] = self.X_pca[:, 0]
        results_df['PC2'] = self.X_pca[:, 1]
        results_df['PC3'] = self.X_pca[:, 2]
        
        # Export vers Excel
        output_path = "resultats_analyse.xlsx"
        results_df.to_excel(output_path, index=False)
        print(f"\nLes résultats ont été exportés vers: {output_path}")
        return results_df

# Modification de l'exécution pour inclure l'export
if __name__ == "__main__":
    analysis = CrispDMAnalysis(data)
    analysis.data_preparation()
    analysis.modeling()
    analysis.evaluation()
    results = analysis.export_results()


