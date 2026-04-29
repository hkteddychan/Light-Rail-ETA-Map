# 🚇 Light Rail ETA Map

輕鐵到站時間地圖 — 每 5 分鐘自動從 rt.data.gov.hk 更新。

## 數據源
- [rt.data.gov.hk Light Rail API](https://rt.data.gov.hk/v1/transport/mtr/lrt/getSchedule)
- [MTR Light Rail Stops CSV](https://opendata.mtr.com.hk/data/light_rail_routes_and_stops.csv)

## 自動更新
GitHub Actions 每 5 分鐘執行 (`cron: '*/5 * * * *'`)

## 輸出格式
```json
{
  "updated": "ISO timestamp",
  "station_count": N,
  "stations": {
    "STOP_CODE": { "platform_list": [...] }
  }
}
```
