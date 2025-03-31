import pickle
import os

PERSISTENCE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'persistence.pickle')

with open(PERSISTENCE_PATH, 'rb') as f:
    data = pickle.load(f)
print("Persistence data:", data)