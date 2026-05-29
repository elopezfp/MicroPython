const state = {
  history: [],
  mode: 'auto',
  setpoint_c: 18,
  fan_speed_pct: 0,
  pump_on: false,
  peltier_power_pct: 0,
  beer_progress_pct: 0,
  beer_ready: false,
  beer_phase: 'Preparando prueba',
  beer_gravity: 1.05,
  elapsed_s: 0,
};

const els = {
  temp: document.getElementById('temperatureValue'),
  tempMirror: document.getElementById('temperatureValueMirror'),
  waterTemp: document.getElementById('waterTempValue'),
  setpoint: document.getElementById('setpointValue'),
  humidity: document.getElementById('humidityValue'),
  beerProgress: document.getElementById('beerProgressValue'),
  beerPhase: document.getElementById('beerPhaseValue'),
  beerPhaseDetail: document.getElementById('beerPhaseDetail'),
  beerGravity: document.getElementById('beerGravityValue'),
  beerProgressFill: document.getElementById('beerProgressFill'),
  beerLiquid: document.getElementById('beerLiquid'),
  beerFoam: document.getElementById('beerFoam'),
  beerElapsed: document.getElementById('beerElapsedValue'),
  pumpStatusInline: document.getElementById('pumpStatusInline'),
  fanStatusInline: document.getElementById('fanStatusInline'),
  peltierStatusInline: document.getElementById('peltierStatusInline'),
  status: document.getElementById('statusText'),
  lastUpdate: document.getElementById('lastUpdate'),
  esp32State: document.getElementById('esp32State'),
  fanStatus: document.getElementById('fanStatus'),
  pumpStatus: document.getElementById('pumpStatus'),
  peltierStatus: document.getElementById('peltierStatus'),
};

function formatTemperature(value) {
  return `${Number(value).toFixed(1)} °C`;
}

function formatPercent(value) {
  return `${Math.round(value || 0)} %`;
}

function updateView(data) {
  Object.assign(state, data);

  els.temp.textContent = formatTemperature(data.temperature_c);
  if (els.tempMirror) {
    els.tempMirror.textContent = `Temperatura real: ${formatTemperature(data.temperature_c)}`;
  }
  els.waterTemp.textContent = formatTemperature(data.water_temp_c);
  els.setpoint.textContent = formatTemperature(data.setpoint_c);
  const spLeft = document.getElementById('setpointLeft');
  if (spLeft) spLeft.textContent = formatTemperature(data.setpoint_c);
  els.humidity.textContent = `${Math.round(data.humidity_pct)} %`;
  if (els.beerProgress) {
    els.beerProgress.textContent = `${Math.round(data.beer_progress_pct || 0)} %`;
  }
  if (els.beerPhase) {
    els.beerPhase.textContent = data.beer_ready ? 'Lista' : (data.beer_phase || 'Fermentando');
  }
  if (els.beerPhaseDetail) {
    els.beerPhaseDetail.textContent = data.beer_ready ? 'Lista' : (data.beer_phase || 'Fermentando');
  }
  if (els.beerGravity) {
    const gravity = Number(data.beer_gravity || 0);
    els.beerGravity.textContent = gravity > 0 ? gravity.toFixed(4) : '0.0000';
  }
  if (els.beerProgressFill) {
    els.beerProgressFill.style.width = `${Math.max(0, Math.min(100, Number(data.beer_progress_pct || 0)))}%`;
  }
  if (els.beerLiquid) {
    const progress = Math.max(0, Math.min(100, Number(data.beer_progress_pct || 0)));
    const fillHeight = 16 + progress * 0.72;
    els.beerLiquid.style.height = `${Math.min(88, fillHeight)}%`;
    els.beerLiquid.style.filter = data.beer_ready ? 'saturate(1.15) brightness(1.02)' : 'none';
  }
  if (els.beerFoam) {
    els.beerFoam.style.bottom = `${16 + Math.max(0, Math.min(100, Number(data.beer_progress_pct || 0))) * 0.62}%`;
  }
  if (els.beerElapsed) {
    els.beerElapsed.textContent = `${Math.round(data.elapsed_s || 0)} s`;
  }
  els.status.textContent = data.status;
  els.lastUpdate.textContent = `Actualizado: ${data.last_update}`;
  els.esp32State.textContent = data.esp32_connected ? 'Conectado' : 'Desconectado';
  els.fanStatus.textContent = formatPercent(data.fan_speed_pct);
  els.pumpStatus.textContent = data.pump_on ? 'Activa' : 'Parada';
  els.peltierStatus.textContent = formatPercent(data.peltier_power_pct);
  if (els.pumpStatusInline) {
    els.pumpStatusInline.textContent = data.pump_on ? 'Activa' : 'Parada';
  }
  if (els.fanStatusInline) {
    els.fanStatusInline.textContent = formatPercent(data.fan_speed_pct);
  }
  if (els.peltierStatusInline) {
    els.peltierStatusInline.textContent = formatPercent(data.peltier_power_pct);
  }
}

async function refreshState() {
  const response = await fetch('/api/state');
  const data = await response.json();
  updateView(data);
}

refreshState();
setInterval(refreshState, 1500);