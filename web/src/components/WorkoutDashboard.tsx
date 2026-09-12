import { useState, useEffect } from 'react';

/**
 * WorkoutDashboard — AI workout plan generator + HRV recovery score display.
 * Consumes /api/v1/workout_plans/generate and /api/v1/workout_plans/recovery.
 */

interface RecoveryData {
  recovery_score: number;
  readiness: string;
  recommendation: string;
  trend: string;
  max_intensity: number;
  volume_multiplier: number;
  notes: string[];
  factors: Record<string, { score: number; weight: number }>;
}

interface PlanResult {
  name: string;
  goal: string;
  duration_weeks: number;
  sessions_per_week: number;
  periodization: string;
  weeks_count: number;
  deload_frequency: number;
}

const GOALS = [
  { value: 'hypertrophy', label: '💪 Muscle Growth', desc: 'Build muscle mass with progressive overload' },
  { value: 'strength', label: '🏋️ Strength', desc: 'Increase max lifts with low rep high weight' },
  { value: 'fat_loss', label: '🔥 Fat Loss', desc: 'Caloric deficit with high intensity training' },
  { value: 'endurance', label: '🏃 Endurance', desc: 'Build stamina with high rep circuits' },
  { value: 'maintenance', label: '⚖️ Maintenance', desc: 'Stay fit with balanced programming' },
];

const EQUIPMENT = [
  { value: 'bodyweight', label: 'Bodyweight' },
  { value: 'dumbbells', label: 'Dumbbells' },
  { value: 'barbell', label: 'Barbell' },
  { value: 'cables', label: 'Cables' },
  { value: 'pull_up_bar', label: 'Pull-up Bar' },
  { value: 'kettlebell', label: 'Kettlebell' },
  { value: 'machine', label: 'Machines' },
  { value: 'resistance_bands', label: 'Resistance Bands' },
];

function ScoreGauge({ score, label }: { score: number; label: string }) {
  const color = score >= 75 ? '#22c55e' : score >= 50 ? '#eab308' : score >= 30 ? '#f97316' : '#ef4444';
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div style={{ textAlign: 'center' }}>
      <svg width="120" height="120" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="#1f2937" strokeWidth="8" />
        <circle
          cx="50" cy="50" r="45" fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 50 50)"
          style={{ transition: 'stroke-dashoffset 1s ease-out' }}
        />
        <text x="50" y="48" textAnchor="middle" fill={color} fontSize="22" fontWeight="700" fontFamily="monospace">
          {Math.round(score)}
        </text>
        <text x="50" y="64" textAnchor="middle" fill="#6b7280" fontSize="9" fontFamily="monospace">
          /100
        </text>
      </svg>
      <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: 4 }}>{label}</div>
    </div>
  );
}

export default function WorkoutDashboard() {
  // Recovery state
  const [recovery, setRecovery] = useState<RecoveryData | null>(null);
  const [loadingRecovery, setLoadingRecovery] = useState(true);

  // Plan generator state
  const [goal, setGoal] = useState('hypertrophy');
  const [experience, setExperience] = useState(5);
  const [age, setAge] = useState(25);
  const [weight, setWeight] = useState(70);
  const [height, setHeight] = useState(175);
  const [sessions, setSessions] = useState(4);
  const [minutes, setMinutes] = useState(60);
  const [weeks, setWeeks] = useState(12);
  const [selectedEquipment, setSelectedEquipment] = useState<string[]>(['barbell', 'dumbbells', 'pull_up_bar']);
  const [planResult, setPlanResult] = useState<PlanResult | null>(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetch('/api/v1/workout_plans/recovery')
      .then(r => r.json())
      .then(data => { setRecovery(data); setLoadingRecovery(false); })
      .catch(() => setLoadingRecovery(false));
  }, []);

  const toggleEquipment = (eq: string) => {
    setSelectedEquipment(prev => prev.includes(eq) ? prev.filter(e => e !== eq) : [...prev, eq]);
  };

  const generatePlan = async () => {
    setGenerating(true);
    try {
      const res = await fetch('/api/v1/workout_plans/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          training_goal: goal,
          experience_level: experience,
          age, weight_kg: weight, height_cm: height,
          max_sessions_per_week: sessions,
          max_minutes_per_session: minutes,
          duration_weeks: weeks,
          available_equipment: selectedEquipment,
        }),
      });
      const data = await res.json();
      setPlanResult(data);
    } catch {}
    setGenerating(false);
  };

  const recommendationColor: Record<string, string> = {
    rest_day: '#ef4444', active_recovery: '#f97316', light_session: '#eab308',
    moderate_session: '#22c55e', high_intensity: '#3b82f6', peak_session: '#a855f7',
  };

  return (
    <div style={{ background: '#0a0e17', minHeight: '100vh', color: '#e5e7eb', fontFamily: "'JetBrains Mono', monospace", padding: '2rem' }}>
      <div style={{ maxWidth: 960, margin: '0 auto' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, background: 'linear-gradient(135deg, #22c55e, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: '0.5rem' }}>
          AdapFit Workout Dashboard
        </h1>
        <p style={{ color: '#6b7280', marginBottom: '2rem' }}>AI-powered training plan generation & recovery tracking</p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
          {/* Recovery Panel */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 12, padding: '1.5rem' }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: '#6b7280', marginBottom: '1rem' }}>
              📊 Today's Recovery
            </div>
            {loadingRecovery ? (
              <div style={{ color: '#6b7280', padding: '2rem', textAlign: 'center' }}>Loading recovery data…</div>
            ) : recovery ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '1rem' }}>
                  <ScoreGauge score={recovery.recovery_score} label="Recovery" />
                  <div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: recommendationColor[recovery.recommendation] || '#22c55e' }}>
                      {recovery.recommendation.replace(/_/g, ' ').toUpperCase()}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: 4 }}>
                      Readiness: {recovery.readiness} • Trend: {recovery.trend}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: 4 }}>
                      Max intensity: {Math.round(recovery.max_intensity * 100)}% • Volume: {Math.round(recovery.volume_multiplier * 100)}%
                    </div>
                  </div>
                </div>
                {recovery.notes.length > 0 && (
                  <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: '#1f2937', borderRadius: 8, fontSize: '0.8rem' }}>
                    {recovery.notes.map((note, i) => <div key={i} style={{ color: '#fbbf24', marginBottom: 2 }}>⚠ {note}</div>)}
                  </div>
                )}
                <div style={{ marginTop: '1rem' }}>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: 6 }}>Factor Breakdown</div>
                  {Object.entries(recovery.factors).map(([key, val]) => (
                    <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ width: 90, fontSize: '0.75rem', color: '#9ca3af' }}>{key}</span>
                      <div style={{ flex: 1, height: 6, background: '#1f2937', borderRadius: 3 }}>
                        <div style={{ height: '100%', width: `${val.score}%`, background: val.score >= 70 ? '#22c55e' : val.score >= 40 ? '#eab308' : '#ef4444', borderRadius: 3, transition: 'width 0.5s' }} />
                      </div>
                      <span style={{ fontSize: '0.75rem', width: 30, textAlign: 'right', color: '#9ca3af' }}>{Math.round(val.score)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ color: '#6b7280', padding: '2rem', textAlign: 'center' }}>No recovery data available</div>
            )}
          </div>

          {/* Plan Generator Panel */}
          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 12, padding: '1.5rem' }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: '#6b7280', marginBottom: '1rem' }}>
              🎯 Generate Workout Plan
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: 6 }}>Training Goal</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {GOALS.map(g => (
                  <button key={g.value} onClick={() => setGoal(g.value)}
                    style={{
                      padding: '8px 12px', borderRadius: 8, border: `1px solid ${goal === g.value ? '#22c55e' : '#1f2937'}`,
                      background: goal === g.value ? 'rgba(34,197,94,0.1)' : '#0a0e17', color: '#e5e7eb',
                      cursor: 'pointer', textAlign: 'left', fontSize: '0.8rem', fontFamily: 'inherit',
                    }}>
                    <span style={{ fontWeight: 600 }}>{g.label}</span>
                    <span style={{ color: '#6b7280', marginLeft: 8 }}>{g.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
              {[
                { label: 'Experience', value: experience, set: setExperience, min: 1, max: 10 },
                { label: 'Age', value: age, set: setAge, min: 14, max: 80 },
                { label: 'Weight (kg)', value: weight, set: setWeight, min: 40, max: 200 },
                { label: 'Height (cm)', value: height, set: setHeight, min: 140, max: 220 },
                { label: 'Sessions/wk', value: sessions, set: setSessions, min: 2, max: 6 },
                { label: 'Min/session', value: minutes, set: setMinutes, min: 20, max: 120 },
              ].map(({ label, value, set, min, max }) => (
                <div key={label}>
                  <div style={{ fontSize: '0.7rem', color: '#6b7280' }}>{label}</div>
                  <input type="range" min={min} max={max} value={value} onChange={e => set(Number(e.target.value))}
                    style={{ width: '100%', accentColor: '#22c55e' }} />
                  <div style={{ fontSize: '0.8rem', textAlign: 'center', fontWeight: 700 }}>{value}</div>
                </div>
              ))}
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: 6 }}>Equipment</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {EQUIPMENT.map(eq => (
                  <button key={eq.value} onClick={() => toggleEquipment(eq.value)}
                    style={{
                      padding: '4px 10px', borderRadius: 6, fontSize: '0.75rem', fontFamily: 'inherit', cursor: 'pointer',
                      border: `1px solid ${selectedEquipment.includes(eq.value) ? '#22c55e' : '#1f2937'}`,
                      background: selectedEquipment.includes(eq.value) ? 'rgba(34,197,94,0.15)' : '#0a0e17',
                      color: selectedEquipment.includes(eq.value) ? '#22c55e' : '#6b7280',
                    }}>
                    {eq.label}
                  </button>
                ))}
              </div>
            </div>

            <button onClick={generatePlan} disabled={generating}
              style={{
                width: '100%', padding: '12px', borderRadius: 8, border: 'none',
                background: generating ? '#1f2937' : 'linear-gradient(135deg, #22c55e, #16a34a)',
                color: '#fff', fontWeight: 700, fontSize: '0.9rem', cursor: generating ? 'wait' : 'pointer',
                fontFamily: 'inherit',
              }}>
              {generating ? '⏳ Generating…' : '🚀 Generate Plan'}
            </button>
          </div>
        </div>

        {/* Plan Result */}
        {planResult && (
          <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: 12, padding: '1.5rem' }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.1em', color: '#6b7280', marginBottom: '1rem' }}>
              ✅ Generated Plan
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#22c55e', marginBottom: 8 }}>{planResult.name}</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: '1rem' }}>
              {[
                { label: 'Duration', value: `${planResult.duration_weeks} weeks` },
                { label: 'Sessions/Week', value: String(planResult.sessions_per_week) },
                { label: 'Periodization', value: planResult.periodization },
                { label: 'Deload', value: `Every ${planResult.deload_frequency} weeks` },
              ].map(({ label, value }) => (
                <div key={label} style={{ padding: '12px', background: '#0a0e17', borderRadius: 8, textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: '#6b7280' }}>{label}</div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 700, marginTop: 4 }}>{value}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
