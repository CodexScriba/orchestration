---
skill_name: greykite
version: "1.0.0"
framework: Python
last_verified: "2026-02-19"
always_attach: false
priority: 7
triggers:
  - greykite
  - silverkite
  - time series forecast
  - anomaly detection
  - changepoint detection
  - linkedin forecasting
---

<!--
LLM INSTRUCTION: This is a skill file for Greykite - LinkedIn's time series forecasting and anomaly detection library.
Apply these patterns when working with Greykite for forecasting, anomaly detection, and changepoint analysis.
-->

# Greykite: Time Series Forecasting & Anomaly Detection

> **Framework:** Greykite (LinkedIn) | **Last Verified:** 2026-02-19

## 1. Overview

Greykite is a Python library developed by LinkedIn for flexible, intuitive, and fast time series forecasting and anomaly detection. The flagship algorithm, Silverkite, excels at handling time series with changepoints in trend or seasonality, event and holiday effects, and temporal dependencies.

### Key Features

- **Multiple algorithms**: Silverkite (native), Facebook Prophet, Auto ARIMA
- **Automatic model selection**: AUTO template for out-of-the-box performance
- **Changepoint detection**: Adaptive lasso with automatic regularization
- **Anomaly detection**: Greykite AD with optimized thresholds
- **Unified interface**: Consistent API across all models
- **Sklearn integration**: Works with scikit-learn pipelines
- **Interactive visualization**: Plotly-based charts

## 2. Core APIs

### 2.1 Forecaster.run_forecast_config - High-level forecasting

The primary entry point for creating forecasts with automatic model selection, cross-validation, and backtesting.

```python
from greykite.common.data_loader import DataLoader
from greykite.framework.templates.autogen.forecast_config import ForecastConfig
from greykite.framework.templates.autogen.forecast_config import MetadataParam
from greykite.framework.templates.forecaster import Forecaster
from greykite.framework.templates.model_templates import ModelTemplateEnum

# Load sample data
data_loader = DataLoader()
df = data_loader.load_peyton_manning()

# Configure metadata
metadata = MetadataParam(
    time_col="ts",
    value_col="y",
    freq="D"
)

# Create forecast configuration
config = ForecastConfig(
    model_template=ModelTemplateEnum.AUTO.name,
    forecast_horizon=365,
    coverage=0.95,
    metadata_param=metadata
)

# Run forecast
forecaster = Forecaster()
result = forecaster.run_forecast_config(df=df, config=config)

# Access results
print(result.forecast.df.head())
print(result.backtest.test_evaluation)
print(result.model[-1].summary())
```

### 2.2 ChangepointDetector.find_trend_changepoints - Detect trend shifts

Identifies points in time where the trend changes using adaptive lasso.

```python
from greykite.algo.changepoint.adalasso.changepoint_detector import ChangepointDetector
from greykite.common.data_loader import DataLoader

# Load data
data_loader = DataLoader()
df = data_loader.load_peyton_manning()

# Initialize detector
detector = ChangepointDetector()

# Detect trend changepoints
result = detector.find_trend_changepoints(
    df=df,
    time_col="ts",
    value_col="y",
    yearly_seasonality_order=10,
    resample_freq="7D",
    potential_changepoint_n=25,
    regularization_strength=0.5,
    actual_changepoint_min_distance="30D",
    no_changepoint_distance_from_end="90D"
)

# View detected changepoints
print(result["trend_changepoints"])

# Visualize
fig = detector.plot()
fig.show()
```

### 2.3 GreykiteDetector - Anomaly detection

Combines forecasting with automatic threshold optimization.

```python
from greykite.detection.detector.config import ADConfig
from greykite.detection.detector.data import DetectorData
from greykite.detection.detector.greykite import GreykiteDetector
from greykite.framework.templates.autogen.forecast_config import ForecastConfig
from greykite.framework.templates.autogen.forecast_config import MetadataParam
from greykite.framework.templates.model_templates import ModelTemplateEnum

# Configure forecast model
metadata = MetadataParam(time_col="ts", value_col="y", freq="D")
forecast_config = ForecastConfig(
    model_template=ModelTemplateEnum.AUTO.name,
    forecast_horizon=7,
    coverage=None,
    metadata_param=metadata
)

# Configure anomaly detection
ad_config = ADConfig(
    volatility_features_list=[
        ["dow"],
        ["is_weekend"],
        ["dow", "hour"]
    ],
    coverage_grid=[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99]
)

# Initialize and train detector
detector = GreykiteDetector(
    forecast_config=forecast_config,
    ad_config=ad_config
)

train_data = DetectorData(df=train_df)
detector.fit(data=train_data)

# Predict anomalies
test_data = DetectorData(df=test_df)
test_data = detector.predict(test_data)

# View results
print(detector.pred_df[["ts", "y", "y_pred", "y_pred_lower", "y_pred_upper", "anomaly"]].head())
```

### 2.4 DataLoader - Sample datasets

Provides easy access to built-in time series datasets.

```python
from greykite.common.data_loader import DataLoader

data_loader = DataLoader()

# View available datasets
print(data_loader.available_datasets)

# Load datasets
df_peyton = data_loader.load_peyton_manning()  # Daily Wikipedia page views
df_bikes = data_loader.load_bikesharing()        # Hourly bike rentals
df_parking = data_loader.load_parking()          # Hourly parking data
```

## 3. Naming Conventions

### 3.1 Variable Naming

| Type | Convention | Example |
|------|-----------|---------|
| DataFrames | `df_*` | `df_raw`, `df_cleaned`, `df_features` |
| Models | `model_*` | `model_forecast`, `model_classifier` |
| Configs | `config_*` | `config_forecast`, `config_ad` |
| Results | `result_*` | `result_forecast`, `result_changepoints` |
| Detectors | `detector_*` | `detector_changepoint`, `detector_anomaly` |
| Metadata | `metadata_*` | `metadata_param` |

### 3.2 Function Naming

```python
# Forecasting functions
def generate_forecast(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Generate time series forecast."""
    pass

def evaluate_forecast(result: ForecastResult) -> dict:
    """Evaluate forecast performance metrics."""
    pass

def plot_forecast(result: ForecastResult) -> go.Figure:
    """Plot forecast with confidence intervals."""
    pass

# Anomaly detection functions
def detect_anomalies(df: pd.DataFrame, config: ADConfig) -> pd.DataFrame:
    """Detect anomalies in time series data."""
    pass

def optimize_thresholds(df: pd.DataFrame, labels: pd.Series) -> dict:
    """Optimize detection thresholds based on labeled data."""
    pass

# Changepoint detection functions
def find_changepoints(df: pd.DataFrame, params: dict) -> list:
    """Find trend changepoints in time series."""
    pass

def plot_changepoints(df: pd.DataFrame, changepoints: list) -> go.Figure:
    """Plot time series with detected changepoints."""
    pass
```

## 4. Common Patterns

### 4.1 Basic Forecasting Workflow

```python
from greykite.common.data_loader import DataLoader
from greykite.framework.templates.autogen.forecast_config import ForecastConfig
from greykite.framework.templates.autogen.forecast_config import MetadataParam
from greykite.framework.templates.forecaster import Forecaster
from greykite.framework.templates.model_templates import ModelTemplateEnum

def run_basic_forecast(
    df: pd.DataFrame,
    time_col: str,
    value_col: str,
    forecast_horizon: int = 30,
    coverage: float = 0.95
) -> ForecastResult:
    """Run basic forecast with AUTO model selection.

    Args:
        df: Input DataFrame with time series data.
        time_col: Name of timestamp column.
        value_col: Name of value column.
        forecast_horizon: Number of periods to forecast.
        coverage: Prediction interval coverage.

    Returns:
        ForecastResult with predictions and metrics.
    """
    # Configure metadata
    metadata = MetadataParam(
        time_col=time_col,
        value_col=value_col,
        freq="D"
    )

    # Create forecast configuration
    config = ForecastConfig(
        model_template=ModelTemplateEnum.AUTO.name,
        forecast_horizon=forecast_horizon,
        coverage=coverage,
        metadata_param=metadata
    )

    # Run forecast
    forecaster = Forecaster()
    result = forecaster.run_forecast_config(df=df, config=config)

    return result
```

### 4.2 Advanced Forecast Configuration

```python
from greykite.framework.templates.autogen.forecast_config import (
    ForecastConfig,
    MetadataParam,
    ModelComponentsParam,
    EvaluationPeriodParam,
    ComputationParam
)

def create_advanced_config(
    forecast_horizon: int = 365,
    coverage: float = 0.95
) -> ForecastConfig:
    """Create advanced forecast configuration with custom parameters.

    Args:
        forecast_horizon: Number of periods to forecast.
        coverage: Prediction interval coverage.

    Returns:
        Configured ForecastConfig object.
    """
    config = ForecastConfig(
        model_template=ModelTemplateEnum.SILVERKITE.name,
        metadata_param=MetadataParam(
            time_col="ts",
            value_col="y",
            freq="D"
        ),
        forecast_horizon=forecast_horizon,
        coverage=coverage,
        model_components_param=ModelComponentsParam(
            growth={"growth_term": "linear"},
            seasonality={
                "yearly_seasonality": 15,
                "quarterly_seasonality": 5,
                "monthly_seasonality": 5,
                "weekly_seasonality": 4
            },
            events={
                "holidays_to_model_separately": ["New Year's Day", "Christmas Day"],
                "holiday_lookup_countries": ["US"],
                "holiday_pre_num_days": 2,
                "holiday_post_num_days": 2
            },
            changepoints={
                "changepoints_dict": {
                    "method": "auto",
                    "regularization_strength": 0.6,
                    "potential_changepoint_n": 25,
                    "no_changepoint_proportion_from_end": 0.2
                }
            },
            autoregression={"autoreg_dict": "auto"}
        ),
        evaluation_period_param=EvaluationPeriodParam(
            test_horizon=90,
            cv_horizon=90,
            cv_min_train_periods=365,
            cv_expanding_window=True,
            cv_periods_between_splits=90
        ),
        computation_param=ComputationParam(
            verbose=1,
            n_jobs=-1
        )
    )

    return config
```

### 4.3 Anomaly Detection Pipeline

```python
from greykite.detection.detector.config import ADConfig
from greykite.detection.detector.data import DetectorData
from greykite.detection.detector.greykite import GreykiteDetector

def run_anomaly_detection(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    time_col: str,
    value_col: str
) -> pd.DataFrame:
    """Run anomaly detection with optimized thresholds.

    Args:
        df_train: Training data for model fitting.
        df_test: Test data for anomaly detection.
        time_col: Name of timestamp column.
        value_col: Name of value column.

    Returns:
        DataFrame with anomaly flags and predictions.
    """
    # Configure forecast model
    metadata = MetadataParam(time_col=time_col, value_col=value_col, freq="D")
    forecast_config = ForecastConfig(
        model_template=ModelTemplateEnum.AUTO.name,
        forecast_horizon=7,
        coverage=None,
        metadata_param=metadata
    )

    # Configure anomaly detection
    ad_config = ADConfig(
        volatility_features_list=[
            ["dow"],
            ["is_weekend"],
            ["dow", "hour"]
        ],
        coverage_grid=[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99]
    )

    # Initialize and train detector
    detector = GreykiteDetector(
        forecast_config=forecast_config,
        ad_config=ad_config
    )

    train_data = DetectorData(df=df_train)
    detector.fit(data=train_data)

    # Predict anomalies
    test_data = DetectorData(df=df_test)
    test_data = detector.predict(test_data)

    return detector.pred_df
```

### 4.4 Changepoint Detection

```python
from greykite.algo.changepoint.adalasso.changepoint_detector import ChangepointDetector

def detect_trend_changepoints(
    df: pd.DataFrame,
    time_col: str,
    value_col: str,
    regularization_strength: float = 0.5
) -> dict:
    """Detect trend changepoints in time series.

    Args:
        df: Input DataFrame with time series data.
        time_col: Name of timestamp column.
        value_col: Name of value column.
        regularization_strength: Regularization strength (0.0-1.0).

    Returns:
        Dictionary with detected changepoints and trend estimation.
    """
    detector = ChangepointDetector()

    result = detector.find_trend_changepoints(
        df=df,
        time_col=time_col,
        value_col=value_col,
        yearly_seasonality_order=10,
        resample_freq="7D",
        potential_changepoint_n=25,
        regularization_strength=regularization_strength,
        actual_changepoint_min_distance="30D",
        no_changepoint_distance_from_end="90D"
    )

    return result
```

## 5. Model Templates

### 5.1 Available Templates

| Template | Description | Use Case |
|----------|-------------|----------|
| `AUTO` | Automatic model selection | Default, unknown data patterns |
| `SILVERKITE` | Native Greykite algorithm | Complex seasonality, changepoints |
| `PROPHET` | Facebook Prophet | Holiday effects, business cycles |
| `ARIMA` | Auto ARIMA | Simple patterns, quick forecasts |

### 5.2 Template Selection

```python
from greykite.framework.templates.model_templates import ModelTemplateEnum

# Automatic selection (recommended for most cases)
config = ForecastConfig(
    model_template=ModelTemplateEnum.AUTO.name,
    ...
)

# Silverkite for complex patterns
config = ForecastConfig(
    model_template=ModelTemplateEnum.SILVERKITE.name,
    ...
)

# Prophet for holiday-heavy data
config = ForecastConfig(
    model_template=ModelTemplateEnum.PROPHET.name,
    ...
)

# ARIMA for simple patterns
config = ForecastConfig(
    model_template=ModelTemplateEnum.ARIMA.name,
    ...
)
```

## 6. Evaluation Metrics

### 6.1 Available Metrics

```python
# Access backtest metrics
result = forecaster.run_forecast_config(df=df, config=config)

# Common metrics
metrics = result.backtest.test_evaluation

# Available metrics:
# - MAPE: Mean Absolute Percentage Error
# - RMSE: Root Mean Squared Error
# - MAE: Mean Absolute Error
# - SMAPE: Symmetric Mean Absolute Percentage Error
# - Quantile losses: For prediction intervals

print(f"MAPE: {metrics['MAPE']:.2f}%")
print(f"RMSE: {metrics['RMSE']:.2f}")
print(f"MAE: {metrics['MAE']:.2f}")
```

### 6.2 Cross-Validation

```python
# Configure cross-validation
config = ForecastConfig(
    ...
    evaluation_period_param=EvaluationPeriodParam(
        test_horizon=90,              # Holdout test set size
        cv_horizon=90,                # Cross-validation fold size
        cv_min_train_periods=365,     # Minimum training size
        cv_expanding_window=True,     # Expanding vs rolling window
        cv_periods_between_splits=90  # Gap between CV splits
    )
)

# Access CV results
result = forecaster.run_forecast_config(df=df, config=config)
cv_results = result.backtest.cv_evaluation
```

## 7. Visualization

### 7.1 Plotting Forecasts

```python
import plotly.io as pio

# Plot timeseries
fig = result.timeseries.plot()
pio.show(fig)

# Plot backtest results
fig_backtest = result.backtest.plot()
pio.show(fig_backtest)

# Plot future forecast
fig_forecast = result.forecast.plot()
pio.show(fig_forecast)

# Plot component breakdown
fig_components = result.forecast.plot_components()
pio.show(fig_components)
```

### 7.2 Plotting Anomalies

```python
# Plot predictions with anomaly flags
fig = detector.plot(phase="predict", title="Anomaly Detection Results")
fig.show()
```

### 7.3 Plotting Changepoints

```python
# Visualize changepoints
fig = detector.plot()
fig.show()
```

## 8. Best Practices

### 8.1 Data Preparation

```python
# Ensure proper column names
df = df.rename(columns={"date": "ts", "value": "y"})

# Ensure proper datetime format
df["ts"] = pd.to_datetime(df["ts"])

# Handle missing values
df = df.dropna(subset=["ts", "y"])

# Sort by time
df = df.sort_values("ts")

# Remove duplicates
df = df.drop_duplicates(subset=["ts"])
```

### 8.2 Model Selection

```python
# Start with AUTO template
config = ForecastConfig(
    model_template=ModelTemplateEnum.AUTO.name,
    ...
)

# If performance is poor, try specific templates
# - SILVERKITE for complex seasonality
# - PROPHET for strong holiday effects
# - ARIMA for simple patterns
```

### 8.3 Hyperparameter Tuning

```python
# Adjust regularization strength for changepoints
config = ForecastConfig(
    ...
    model_components_param=ModelComponentsParam(
        changepoints={
            "changepoints_dict": {
                "regularization_strength": 0.6,  # Higher = fewer changepoints
                "potential_changepoint_n": 25
            }
        }
    )
)

# Adjust seasonality orders
config = ForecastConfig(
    ...
    model_components_param=ModelComponentsParam(
        seasonality={
            "yearly_seasonality": 15,  # Higher = more flexible
            "weekly_seasonality": 4
        }
    )
)
```

### 8.4 Performance Optimization

```python
# Use parallel processing
config = ForecastConfig(
    ...
    computation_param=ComputationParam(
        n_jobs=-1  # Use all cores
    )
)

# Reduce CV folds for faster training
config = ForecastConfig(
    ...
    evaluation_period_param=EvaluationPeriodParam(
        cv_horizon=30,  # Smaller folds
        cv_periods_between_splits=30
    )
)
```

## 9. Common Use Cases

### 9.1 Business Metric Forecasting

```python
def forecast_business_metric(
    df: pd.DataFrame,
    metric_name: str,
    forecast_horizon: int = 90
) -> dict:
    """Forecast business metrics like revenue, users, etc.

    Args:
        df: Historical metric data.
        metric_name: Name of the metric being forecasted.
        forecast_horizon: Number of periods to forecast.

    Returns:
        Dictionary with forecast and metrics.
    """
    result = run_basic_forecast(
        df=df,
        time_col="ts",
        value_col="y",
        forecast_horizon=forecast_horizon
    )

    return {
        "metric_name": metric_name,
        "forecast": result.forecast.df,
        "metrics": result.backtest.test_evaluation,
        "model_summary": result.model[-1].summary()
    }
```

### 9.2 Monitoring Anomaly Detection

```python
def detect_monitoring_anomalies(
    df: pd.DataFrame,
    metric_name: str,
    train_ratio: float = 0.8
) -> pd.DataFrame:
    """Detect anomalies in monitoring metrics.

    Args:
        df: Time series monitoring data.
        metric_name: Name of the metric.
        train_ratio: Ratio of data to use for training.

    Returns:
        DataFrame with anomaly flags.
    """
    split_idx = int(len(df) * train_ratio)
    df_train = df[:split_idx].reset_index(drop=True)
    df_test = df[split_idx:].reset_index(drop=True)

    result = run_anomaly_detection(
        df_train=df_train,
        df_test=df_test,
        time_col="ts",
        value_col="y"
    )

    return result
```

### 9.3 Hierarchical Forecast Reconciliation

```python
from greykite.algo.reconcile.convex.reconcile_forecasts import ReconcileAdditiveForecasts

def reconcile_hierarchical_forecasts(
    forecasts_df: pd.DataFrame,
    constraint_matrix: pd.DataFrame
) -> pd.DataFrame:
    """Reconcile hierarchical forecasts to satisfy additivity constraints.

    Args:
        forecasts_df: DataFrame with hierarchical forecasts.
        constraint_matrix: Constraint matrix defining relationships.

    Returns:
        Reconciled forecasts satisfying constraints.
    """
    reconciler = ReconcileAdditiveForecasts()

    reconciled = reconciler.reconcile_forecasts(
        forecasts=forecasts_df,
        constraint_matrix=constraint_matrix,
        unbiased=True,
        weight="MLE"
    )

    return reconciled["reconciled_forecasts"]
```

## 10. Quick Reference

### 10.1 Import Patterns

```python
# Core imports
from greykite.common.data_loader import DataLoader
from greykite.framework.templates.forecaster import Forecaster
from greykite.framework.templates.autogen.forecast_config import (
    ForecastConfig,
    MetadataParam,
    ModelComponentsParam
)
from greykite.framework.templates.model_templates import ModelTemplateEnum

# Changepoint detection
from greykite.algo.changepoint.adalasso.changepoint_detector import ChangepointDetector

# Anomaly detection
from greykite.detection.detector.greykite import GreykiteDetector
from greykite.detection.detector.config import ADConfig
from greykite.detection.detector.data import DetectorData

# Reconciliation
from greykite.algo.reconcile.convex.reconcile_forecasts import ReconcileAdditiveForecasts
```

### 10.2 Common Parameters

| Parameter | Description | Default | Common Values |
|-----------|-------------|---------|---------------|
| `forecast_horizon` | Periods to forecast | - | 30, 90, 365 |
| `coverage` | Prediction interval | 0.95 | 0.8, 0.9, 0.95, 0.99 |
| `regularization_strength` | Changepoint regularization | 0.6 | 0.3, 0.5, 0.7, 0.9 |
| `yearly_seasonality` | Fourier order for yearly | 15 | 5, 10, 15, 20 |
| `weekly_seasonality` | Fourier order for weekly | 4 | 2, 4, 6, 8 |

### 10.3 Result Access

```python
# Forecast results
result.forecast.df              # Future predictions
result.forecast.plot()          # Plot forecast
result.forecast.plot_components()  # Plot components

# Backtest results
result.backtest.test_evaluation  # Test set metrics
result.backtest.cv_evaluation    # CV metrics
result.backtest.plot()           # Plot backtest

# Model results
result.model[-1].summary()       # Model summary
result.model.predict(df)         # Make predictions
result.timeseries.make_future_dataframe(periods=30)  # Future dates
```

## 11. Troubleshooting

### 11.1 Common Issues

**Issue: Poor forecast accuracy**
- Solution: Try different model templates (SILVERKITE, PROPHET)
- Solution: Adjust seasonality orders
- Solution: Check for data quality issues

**Issue: Too many/few changepoints**
- Solution: Adjust `regularization_strength` (higher = fewer)
- Solution: Set `potential_changepoint_n` appropriately
- Solution: Use `actual_changepoint_min_distance`

**Issue: Too many false anomalies**
- Solution: Adjust `coverage_grid` range
- Solution: Add volatility features
- Solution: Use labeled data for threshold optimization

**Issue: Slow training**
- Solution: Use `n_jobs=-1` for parallel processing
- Solution: Reduce CV folds
- Solution: Use simpler model template

### 11.2 Debugging Tips

```python
# Enable verbose output
config = ForecastConfig(
    ...
    computation_param=ComputationParam(verbose=2)
)

# Check data quality
print(df.info())
print(df.describe())
print(df.isnull().sum())

# Validate model fit
model = result.model[-1]
print(model.summary())

# Plot residuals
fig = result.forecast.plot_components()
pio.show(fig)
```
