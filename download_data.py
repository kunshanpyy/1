import kagglehub

# Download latest version
path = kagglehub.dataset_download("yuriisavinskyi/livecell-dataset-2021")

print("Path to dataset files:", path)