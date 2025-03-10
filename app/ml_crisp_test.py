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

data = "C:/Users/aoruezabal/Downloads/Untitled discover search(5).csv"

df = pd.read_csv(data, sep=",")

class CrispDMAnalysis:
    def __init__(self, data_path):
        self.df = pd.read_csv(data_path, sep=",")
        
    def data_preparation(self):
        # Sélection des variables numériques
        numeric_cols = self.df.select_dtypes(include=['float64', 'int64']).columns
        X = self.df[numeric_cols]
        
        # Imputation des valeurs manquantes
        imputer = SimpleImputer(strategy='mean')
        self.X_imputed = imputer.fit_transform(X)
        
        # Standardisation avec StandardScaler
        scaler = StandardScaler()
        self.X_scaled = scaler.fit_transform(self.X_imputed)
        
        return self.X_scaled
        
    def modeling(self):
        # ACP pour la réduction de dimension
        self.pca = PCA(n_components=2)
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
        """Visualisation des résultats"""
        fig = plt.figure(figsize=(15, 5))
        
        # Plot ACP avec clusters
        plt.subplot(1, 3, 1)
        plt.scatter(self.X_pca[:, 0], self.X_pca[:, 1], c=self.clusters, cmap='viridis')
        plt.title('Segmentation (ACP + K-means)')
        
        # Plot des anomalies
        plt.subplot(1, 3, 2)
        plt.scatter(self.X_pca[:, 0], self.X_pca[:, 1], c=self.anomalies, cmap='RdYlBu')
        plt.title('Détection d\'anomalies')
        
        # Plot variance expliquée
        plt.subplot(1, 3, 3)
        plt.bar(range(len(self.pca.explained_variance_ratio_)), 
                self.pca.explained_variance_ratio_)
        plt.title('Variance expliquée par composante')
        
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

# Exécution de l'analyse
if __name__ == "__main__":
    analysis = CrispDMAnalysis(data)
    analysis.data_preparation()
    analysis.modeling()
    analysis.evaluation()


