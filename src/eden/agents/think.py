from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from eden.integrations.rtdb import community_path, ref


class ThinkAgent:
    """Energy forecasting over sensed data; `run` is the entrypoint used by the think service."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_ref = ref(db_path or community_path("sense_data"))
        self.energy_model: Optional[RandomForestRegressor] = None

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: connect payload to the training/prediction loop.
        return {
            "message": "Thinking...",
            "receivedKeys": list(payload.keys()) if isinstance(payload, dict) else [],
        }

    def fetch_data(self) -> pd.DataFrame:
        raw_data = self.db_ref.get()
        if not raw_data:
            raise ValueError("No data found in Firebase")

        df = pd.DataFrame(list(raw_data.values()))
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["hour"] = df["timestamp"].dt.hour
        else:
            # Model depends on hour
            df["hour"] = 0
        return df

    def train_energy_model(self, df: pd.DataFrame) -> None:
        features = ["temperature", "humidity", "hour"]
        missing = [c for c in features + ["energy_usage"] if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns for training: {missing}")

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(df[features], df["energy_usage"])
        self.energy_model = model

    def predict_next(self, latest_row: pd.Series) -> float:
        if not self.energy_model:
            raise RuntimeError("Energy model not trained. Call train_energy_model first.")

        X = [[
            float(latest_row["temperature"]),
            float(latest_row["humidity"]),
            float(latest_row["hour"]),
        ]]
        return float(self.energy_model.predict(X)[0])

    @staticmethod
    def generate_recommendation(predicted_energy: float) -> str:
        if predicted_energy > 8:
            return "Shift operations to off-peak or reduce non-critical loads."
        return "Energy usage within safe limits."


if __name__ == "__main__":
    agent = ThinkAgent()
    df = agent.fetch_data()
    agent.train_energy_model(df)

    prediction = agent.predict_next(df.sort_values("timestamp").iloc[-1])
    print(f"Predicted next energy usage: {prediction:.2f} kWh")
    print("Recommendation:", agent.generate_recommendation(prediction))
