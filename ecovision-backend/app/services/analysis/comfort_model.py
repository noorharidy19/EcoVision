import tensorflow as tf
import numpy as np
import json
import os

class EcoVisionModelService:
    def __init__(self, model_path: str):
        print("Loading EcoVision model... ⏳")
        self.model = tf.keras.models.load_model(model_path)
        print("Model loaded ✅")
        print(self.model.summary())

    def clean_and_fix_json(self, data, orientation='South'):
        data['furniture'] = []
        data['windows'] = []

        for room in data['rooms']:
            b = room['bounds']
            if orientation == 'South':
                coords = [room['centroid'][0], b['max_y']]
            elif orientation == 'North':
                coords = [room['centroid'][0], b['min_y']]
            elif orientation == 'East':
                coords = [b['max_x'], room['centroid'][1]]
            elif orientation == 'West':
                coords = [b['min_x'], room['centroid'][1]]

            data['windows'].append({
                "parent_id": room['id'],
                "coords": coords
            })
        return data

    def run_inference_for_orientation(self, raw_data: dict, orient: str):
        data = self.clean_and_fix_json(raw_data, orientation=orient)

        img = np.zeros((256, 256, 2), dtype=np.float32)
        all_x = [r['bounds']['min_x'] for r in data['rooms']] + [r['bounds']['max_x'] for r in data['rooms']]
        all_y = [r['bounds']['min_y'] for r in data['rooms']] + [r['bounds']['max_y'] for r in data['rooms']]

        min_x, min_y = min(all_x), min(all_y)
        width, height = max(all_x) - min_x, max(all_y) - min_y
        max_dim = max(width, height)
        scale = 220.0 / max_dim if max_dim > 0 else 1.0

        for room in data['rooms']:
            b = room['bounds']
            x1, x2 = int((b['min_x'] - min_x) * scale) + 18, int((b['max_x'] - min_x) * scale) + 18
            y1, y2 = int((b['min_y'] - min_y) * scale) + 18, int((b['max_y'] - min_y) * scale) + 18
            img[max(0, y1):min(256, y2), max(0, x1):min(256, x2), 0] = 1.0

        for win in data['windows']:
            wx, wy = int((win['coords'][0] - min_x) * scale) + 18, int((win['coords'][1] - min_y) * scale) + 18
            img[max(0, wy-3):min(256, wy+3), max(0, wx-3):min(256, wx+3), 1] = 1.0

        # Climate normalization example (Cairo)
        raw_avg_temp, raw_max_temp, raw_solar = 38.0, 47.4, 275.26
        n_avg = (raw_avg_temp - 20.0) / 7.0
        n_max = (raw_max_temp - 30.0) / 18.0
        n_solar = (raw_solar - 230.0) / 50.0
        climate_features = np.array([[n_avg, n_max, n_solar]])

        return np.expand_dims(img, axis=0), climate_features

    def predict(self, json_data: dict):
        results = {}
        orientations = ['North', 'South', 'East', 'West']
        for orient in orientations:
            cnn_in, mlp_in = self.run_inference_for_orientation(json_data, orient)
            preds = self.model.predict([cnn_in, mlp_in], verbose=0)
            t_score, v_score = preds[0][0][0] * 100, preds[1][0][0] * 100
            results[orient] = {"thermal": round(t_score, 1), "visual": round(v_score, 1)}
        return results
