import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

class DataUnderstanding:
    def __init__(self, data_path):
        self.data = pd.read_csv(data_path)
        # Remove columns containing 'keyword' in their name
        keyword_cols = [col for col in self.data.columns if 'keyword' in col.lower()]
        self.data = self.data.drop(columns=keyword_cols)
        
    def explore_data(self):
        print("Data Shape:", self.data.shape)
        print("/nData Info:")
        print(self.data.info())
        print("/nMissing Values:")
        print(self.data.isnull().sum())

class DataPreparation:
    def __init__(self, data):
        self.data = data
        self.scaler = StandardScaler()
        
    def prepare_data(self):
        
        # Handle missing values
        self.data = self.data.fillna(self.data.mean())
        
        # Scale numerical features
        numerical_cols = self.data.select_dtypes(include=[np.number]).columns
        self.data[numerical_cols] = self.scaler.fit_transform(self.data[numerical_cols])
        
        return self.data

class Modeling:
    def __init__(self, data):
        self.data = data
        
    def perform_pca(self, n_components=2):
        pca = PCA(n_components=n_components)
        pca_result = pca.fit_transform(self.data)
        print("Explained variance ratio:", pca.explained_variance_ratio_)
        return pca_result
    
    def perform_clustering(self, n_clusters=3):
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(self.data)
        return clusters

class Evaluation:
    def evaluate_clusters(self, data, clusters):
        plt.figure(figsize=(10, 6))
        plt.scatter(data[:, 0], data[:, 1], c=clusters)
        plt.title('Cluster Analysis Results')
        plt.xlabel('First Principal Component')
        plt.ylabel('Second Principal Component')
        plt.show()

class CRISPDMAnalysis:
    def __init__(self, data_path):
        self.data_path = data_path
        
    def run_analysis(self):
        
        # Data Understanding
        data_understanding = DataUnderstanding(self.data_path)
        data_understanding.explore_data()
        
        # Data Preparation
        prep = DataPreparation(data_understanding.data)
        prepared_data = prep.prepare_data()
        
        # Modeling
        modeling = Modeling(prepared_data)
        pca_results = modeling.perform_pca()
        clusters = modeling.perform_clustering()
        
        # Evaluation
        evaluation = Evaluation()
        evaluation.evaluate_clusters(pca_results, clusters)
        
        return {
            'pca_results': pca_results,
            'clusters': clusters,
            'prepared_data': prepared_data
        }

if __name__ == "__main__":
    analysis = CRISPDMAnalysis("C:/Users/aoruezabal/Downloads/Untitled discover search(4).csv")
    results = analysis.run_analysis()



