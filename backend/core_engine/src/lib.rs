use pyo3::prelude::*;

/// Compute HRV Z-Score: (today_hrv - baseline_mean) / baseline_std
/// Returns (z_score, normalized_score_0_to_100)
#[pyfunction]
fn compute_hrv_zscore(today_hrv: f64, baseline_mean: f64, baseline_std: f64) -> (f64, f64) {
    let std = if baseline_std > 0.1 { baseline_std } else { 10.0 };
    let z_score = (today_hrv - baseline_mean) / std;
    let mut hrv_score = 50.0 + (z_score * 25.0);
    hrv_score = hrv_score.clamp(0.0, 100.0);
    ((z_score * 100.0).round() / 100.0, (hrv_score * 10.0).round() / 10.0)
}

/// Compute Sleep Quality Index (0-100)
#[pyfunction]
fn compute_sleep_score(sleep_hours: f64, efficiency: f64, target_hours: f64) -> f64 {
    let duration_ratio = (sleep_hours / target_hours).min(1.0);
    let duration_score = duration_ratio * 100.0;
    let eff = efficiency.clamp(0.0, 100.0);
    let score = 0.70 * duration_score + 0.30 * eff;
    (score.clamp(0.0, 100.0) * 10.0).round() / 10.0
}

/// Compute ACWR: returns (acwr_value, status_string, penalty_modifier)
#[pyfunction]
fn compute_acwr(acute_load: f64, chronic_load: f64) -> (f64, String, f64) {
    if chronic_load <= 0.0 {
        return (1.0, "SWEET_SPOT".to_string(), 0.0);
    }
    let acwr = ((acute_load / chronic_load) * 100.0).round() / 100.0;
    if acwr < 0.80 {
        (acwr, "UNDER_TRAINING".to_string(), 0.0)
    } else if acwr <= 1.30 {
        (acwr, "SWEET_SPOT".to_string(), 0.0)
    } else if acwr < 1.50 {
        (acwr, "CAUTION".to_string(), -5.0)
    } else {
        (acwr, "DANGER_ZONE".to_string(), -15.0)
    }
}

/// Exponentially Weighted Moving Average
#[pyfunction]
fn compute_ewma(values: Vec<f64>, window: usize) -> Vec<f64> {
    if values.is_empty() {
        return vec![];
    }
    let alpha = 2.0 / (window as f64 + 1.0);
    let mut result = Vec::with_capacity(values.len());
    result.push(values[0]);
    for i in 1..values.len() {
        let ewma = alpha * values[i] + (1.0 - alpha) * result[i - 1];
        result.push((ewma * 100.0).round() / 100.0);
    }
    result
}

/// Compute composite recovery score (0-100)
#[pyfunction]
fn compute_recovery_score(
    hrv_score: f64,
    sleep_score: f64,
    subj_score: f64,
    acwr_penalty: f64,
    has_hrv: bool,
) -> i32 {
    let raw = if has_hrv {
        0.40 * hrv_score + 0.35 * sleep_score + 0.25 * subj_score + acwr_penalty
    } else {
        0.55 * sleep_score + 0.45 * subj_score + acwr_penalty
    };
    raw.clamp(0.0, 100.0).round() as i32
}

/// Z-score anomaly detection on a time series
#[pyfunction]
fn detect_anomalies(values: Vec<f64>, threshold: f64) -> Vec<bool> {
    if values.len() < 3 {
        return vec![false; values.len()];
    }
    let n = values.len() as f64;
    let mean: f64 = values.iter().sum::<f64>() / n;
    let variance: f64 = values.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / n;
    let std = variance.sqrt();
    if std < 0.001 {
        return vec![false; values.len()];
    }
    values.iter().map(|v| ((v - mean) / std).abs() > threshold).collect()
}

/// Multi-factor injury risk score (0-100)
#[pyfunction]
fn detect_injury_risk(
    acwr: f64,
    hrv_trend_slope: f64,
    sleep_debt_hours: f64,
    consecutive_high_load_days: i32,
) -> f64 {
    let mut risk = 0.0f64;
    // ACWR contribution (0-35 points)
    if acwr > 1.5 { risk += 35.0; }
    else if acwr > 1.3 { risk += 20.0; }
    else if acwr < 0.8 { risk += 10.0; }
    // HRV declining trend (0-25 points)
    if hrv_trend_slope < -2.0 { risk += 25.0; }
    else if hrv_trend_slope < -1.0 { risk += 15.0; }
    else if hrv_trend_slope < -0.5 { risk += 8.0; }
    // Sleep debt (0-20 points)
    if sleep_debt_hours > 4.0 { risk += 20.0; }
    else if sleep_debt_hours > 2.0 { risk += 12.0; }
    else if sleep_debt_hours > 1.0 { risk += 6.0; }
    // Consecutive high load days (0-20 points)
    if consecutive_high_load_days >= 5 { risk += 20.0; }
    else if consecutive_high_load_days >= 3 { risk += 12.0; }
    else if consecutive_high_load_days >= 2 { risk += 6.0; }
    (risk.clamp(0.0, 100.0) * 10.0).round() / 10.0
}

/// Compute subjective score from Hooper-Mackinnon ratings
#[pyfunction]
fn compute_subjective_score(
    soreness: i32,
    fatigue: i32,
    stress: i32,
    num_sore_groups: i32,
) -> f64 {
    let sore = soreness.clamp(1, 10) as f64;
    let energy = fatigue.clamp(1, 10) as f64;
    let stress_inv = (11 - stress.clamp(1, 10)) as f64;
    let muscle_penalty = if num_sore_groups == 0 {
        10.0
    } else {
        (10.0 - num_sore_groups as f64 * 2.0).max(2.0)
    };
    let total = sore + energy + stress_inv + muscle_penalty;
    ((total / 40.0 * 100.0).clamp(0.0, 100.0) * 10.0).round() / 10.0
}

#[pymodule]
fn core_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_hrv_zscore, m)?)?;
    m.add_function(wrap_pyfunction!(compute_sleep_score, m)?)?;
    m.add_function(wrap_pyfunction!(compute_acwr, m)?)?;
    m.add_function(wrap_pyfunction!(compute_ewma, m)?)?;
    m.add_function(wrap_pyfunction!(compute_recovery_score, m)?)?;
    m.add_function(wrap_pyfunction!(detect_anomalies, m)?)?;
    m.add_function(wrap_pyfunction!(detect_injury_risk, m)?)?;
    m.add_function(wrap_pyfunction!(compute_subjective_score, m)?)?;
    Ok(())
}
