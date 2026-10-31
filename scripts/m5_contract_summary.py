"""Offline smoke for M5 preview, no network or paid calls. Requires M3 source."""
from fastapi.testclient import TestClient
from eden.sentinel.m5_readonly import app

client=TestClient(app)
assert client.get('/health').json()['control_mode']=='read_only'
scenarios=client.get('/m3/scenarios').json()
for name in scenarios:
    response=client.get('/m3/evaluate/'+name)
    response.raise_for_status()
    result=response.json()
    summary=result['realized']
    print(f'{name}: essential delta={summary["essential_unserved_reduction_kwh"]:.4f} kWh, '
          f'flexible delta={summary["flexible_unserved_reduction_kwh"]:.4f} kWh, '
          f'reserve violations={summary["battery_reserve_violations"]}')
    assert result['mode']=='simulation'
    assert summary['battery_reserve_violations']==0
assert client.post('/m4/proposals',json={}).status_code==404
print('PASS: read-only preview contract; no M4 execution endpoints')
