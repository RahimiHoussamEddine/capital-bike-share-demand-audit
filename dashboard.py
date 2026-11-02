"""Aggregate-only Streamlit dashboard."""

from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from bike_share_audit.constants import REPORTS_DIR
from bike_share_audit.modeling import MODEL_LABELS

st.set_page_config(page_title="Bike-share demand audit", layout="wide")
st.title("Capital Bikeshare hourly demand audit")
st.caption(
    "Historical system-wide rental counts, evaluated with a rolling one-hour "
    "forecast and a chronological holdout."
)

summary_path = REPORTS_DIR / "summary.json"
if not summary_path.exists():
    st.info("Build the report first with `make build`.")
    st.stop()

summary = json.loads(summary_path.read_text(encoding="utf-8"))
quality = json.loads((REPORTS_DIR / "data_quality.json").read_text(encoding="utf-8"))
metrics = pd.read_csv(REPORTS_DIR / "model_metrics.csv")
hourly = pd.read_csv(REPORTS_DIR / "hourly_error.csv")
monthly = pd.read_csv(REPORTS_DIR / "monthly_metrics.csv")

left, middle, right = st.columns(3)
left.metric("Source hourly rows", f"{summary['rows']:,}")
middle.metric("Missing clock-hour slots", quality["missing_hour_slots"])
right.metric("Target total", f"{quality['target_sum']:,} rentals")

metric_options = {
    "mae": "Mean absolute error",
    "rmse": "Root mean squared error",
    "wape": "Weighted absolute percentage error",
}
metric = st.selectbox(
    "Test metric",
    list(metric_options),
    format_func=metric_options.get,
)
model_data = metrics.copy()
model_data["model_label"] = model_data["model"].map(MODEL_LABELS)
model_chart = px.bar(
    model_data,
    x="model_label",
    y=metric,
    labels={"model_label": "Forecast method", metric: metric_options[metric]},
    title="Chronological test metrics",
)
st.plotly_chart(model_chart, width="stretch")

selected_model = st.selectbox(
    "Model detail",
    list(MODEL_LABELS),
    format_func=MODEL_LABELS.get,
)
hourly_data = hourly[hourly["model"] == selected_model]
hour_chart = px.line(
    hourly_data,
    x="hour",
    y="mae",
    markers=True,
    labels={"hour": "Hour of day", "mae": "MAE (rentals)"},
    title="Absolute forecast error by hour of day",
)
st.plotly_chart(hour_chart, width="stretch")

monthly_data = monthly.copy()
monthly_data["model_label"] = monthly_data["model"].map(MODEL_LABELS)
monthly_chart = px.line(
    monthly_data,
    x="month",
    y="mae",
    color="model_label",
    markers=True,
    labels={"month": "Test month", "mae": "MAE (rentals)", "model_label": "Model"},
    title="Monthly test error",
)
st.plotly_chart(monthly_chart, width="stretch")

split_summary = pd.read_csv(REPORTS_DIR / "split_summary.csv")
st.dataframe(split_summary, hide_index=True, width="stretch")
st.markdown(
    "The model uses only calendar information and past rental counts. It does "
    "not report station availability or use same-hour observed weather."
)
