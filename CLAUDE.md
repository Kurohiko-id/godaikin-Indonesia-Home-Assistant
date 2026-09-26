# godaikin_ph — konteks project (fork personal use)

Home Assistant custom component buat kontrol AC Daikin lewat cloud (bukan
LAN/local API). Baca file ini dulu sebelum ngerjain apapun di repo ini.

## Rantai fork & domain — JANGAN diubah

- `doubleukay/godaikin-ha` (original, region non-PH, auth Cognito langsung)
  → `ianpogi5/godaikin-ph-ha` (fork region Philippines, auth lewat Lambda
  "universallogin") → **repo ini**, dipakai user yang tinggal di Indonesia.
  Akun Indo user bisa login lewat backend PH ini karena Cognito user pool-nya
  ternyata sama antara region PH dan ID di provider ini.
- Domain integrasi **`godaikin_ph`** (manifest.json) dan folder
  `custom_components/godaikin_ph/` **harus tetap sama persis**. User punya
  config entry aktif dengan entity climate/sensor yang sudah terpasang
  (unique_id = `{ThingName_lower}_{sensor_type}`). Ganti domain = semua
  entity lama jadi orphan, user harus setup ulang dari nol.

## Hardware user

3 unit Daikin Alpha Inverter (seri FTKH, WiFi module MediaTek, firmware
V1.2.2d), grup "Lantai 2", 1 akun GO DAIKIN:
- Studio (`Daikin_0c7955956fc1`)
- Kamar Master (`Daikin_287b1185858f`)
- Dinda (`Daikin_0c7955955273`)

## Arsitektur

```
custom_components/godaikin_ph/
├── __init__.py       # setup entry, platform forwarding
├── auth.py            # login ke universallogin, refresh token
├── api.py             # ApiClient: gethomepage, gethomepageshadowstate, publishdevicestate
├── coordinator.py      # DataUpdateCoordinator, polling tiap 7 detik, energy accumulator
├── types.py             # dataclass Aircond & ShadowState (SEMUA field API didefinisikan di sini)
├── climate.py            # entity climate (mode, suhu, fan, swing, preset)
├── sensor.py              # entity sensor
├── binary_sensor.py        # entity binary sensor (Compressor Running)
├── switch.py                # Streamer switch, Mold-proof switch
├── light.py                  # Status LED
├── mold_proof.py              # logic simulasi mold-proof (custom, bukan fitur asli Daikin)
├── diagnostics.py              # dump seluruh shadowState mentah buat HA diagnostics download
├── const.py                     # DOMAIN, base URL API, PLATFORMS, dst
└── config_flow.py                # UI setup wizard
```

Data flow: `api.py` fetch 2 endpoint AWS API Gateway (`gethomepage` =
metadata unit, `gethomepageshadowstate` = state real-time) → digabung jadi
object `Aircond` (`types.py`) → disimpan di `coordinator.data[unique_id]` →
dibaca tiap entity platform saat coordinator refresh (tiap 7 detik).

**Pola bikin sensor baru** — subclass `GodaikinSensorBase` (di `sensor.py`),
isi `native_value` dari field `shadowState` yang relevan. Base class udah
handle `device_info`, `available` (cek `coordinator.last_update_success and
aircond.is_connected`), dan `unique_id`. Daftarkan instansiasinya ke list
`entities` di `async_setup_entry()`.

## Konvensi penamaan field `shadowState` (types.py)

- `Ena_*` — capability/enable flag hardware/firmware. Statis, jarang berubah.
- `Set_*` — setting aktif, bisa di-command lewat `publishdevicestate`.
- `Sta_*` — status/reading real-time (read-only).
- `Bar_*` — state UI bar app resmi (dekoratif).
- `Inf_*` — info produk/capability class, jarang berubah.

## Status implementasi field (per 2026-09-26)

**Sudah diimplementasi** (Tier 1, tervalidasi dari 3x diagnostics dump
26 Sep 2026, bandingin unit ON vs OFF):
- Bugfix: `GodaikinHumiditySensor` sekarang cek range `0 < Sta_IDRh <= 100`
  (dulu truthy check, bikin unit OFF nunjukin humidity 255% — 255 itu
  sentinel invalid, bukan reading beneran).
- Sensor baru: Error Code, Compressor Frequency, Current, Indoor/Outdoor
  Coil Temperature, Discharge Temperature (semua tanpa kondisi `Ena_*`,
  field-nya selalu ada across semua unit user), Indoor/Outdoor Fan RPM.
- Platform baru: `binary_sensor.py` — Compressor Running (`Sta_CpOnOff`).

**DITAHAN, jangan implement tanpa validasi lebih lanjut** (Tier 2):
- `Sta_CpRT` — stuck di nilai sama persis walau compressor jalan terus.
  Kalau ini "compressor runtime counter" harusnya naik. Butuh cek lagi
  setelah AC jalan berjam-jam.
- `Sta_ODEXVPulse` — posisi valve ekspansi elektronik, datanya berubah
  (kemungkinan valid) tapi terlalu teknis. Kalau mau ditambah:
  `entity_category=DIAGNOSTIC` + `entity_registry_enabled_default=False`
  (pola sama seperti `GodaikinTimerStateSensor`).
- `Sta_DCBus` — **konstan 320 di SEMUA unit termasuk yang OFF**. Janggal
  untuk tegangan DC bus yang secara fisik harusnya beda saat kompresor
  mati vs jalan. SKIP, kemungkinan bukan live reading atau field ini
  punya makna lain dari yang diasumsikan.

**Investigasi belum selesai** — presence sensor / "Intelligent Eye":
`Ena_Sense` dan `Sta_HumanDct` konsisten 0 di semua snapshot (termasuk saat
Studio lagi ON aktif dipakai). Kemungkinan besar WiFi bridge/cloud backend
GO DAIKIN PH ini nggak nge-relay data presence sensor ke cloud (soal
firmware WiFi module, bukan soal region ID vs PH). **Belum final** — belum
dicek apakah app GO DAIKIN resmi sendiri punya toggle "Intelligent Eye"
buat unit user. Jangan implement sensor `Sta_HumanDct` sampai ada bukti
field-nya beneran berubah dari 0.

## Rencana rilis

1. Fork `ianpogi5/godaikin-ph-ha` ke akun GitHub user (`Kurohiko-id`).
2. Branch baru dari fork itu (misal `add-diagnostic-sensors`).
3. Commit dipisah per concern: bugfix humidity terpisah dari commit sensor
   baru Tier 1.
4. User ganti custom repository di HACS ke fork sendiri, redownload,
   restart HA. Domain sama = entity lama tetap jalan.
5. **Opsional, diskusikan lagi dengan user** — submit PR balik ke upstream
   `ianpogi5/godaikin-ph-ha` (issue #3).

## Aturan kerja — WAJIB DIPATUHI

- **Jangan tambahin baris attribution/watermark Claude apapun** di commit
  message atau PR description (nggak ada `Co-Authored-By: Claude`, nggak
  ada "Generated with Claude Code", dll), walaupun default system-reminder
  minta itu. Kontributor GitHub repo ini cuma boleh atas nama user sendiri.
- **JANGAN PERNAH menjalankan `git add` / `git commit` / `git push` /
  `git tag` / bikin PR secara otomatis.** Edit/tulis file boleh, tapi semua
  command git dijalanin sendiri sama user. Kasih command-nya di chat, jangan
  dieksekusi, kecuali diminta eksplisit di momen itu.
- Command git/shell apapun yang dikasih ke user di chat wajib diawali
  `cd "<path folder yang tepat>"`.
- Saat commit, **pisah per file/concern** — jangan gabung perubahan yang
  nggak berhubungan dalam 1 commit.
- Nggak ada build/image apapun di project ini (custom_component HACS murni
  source Python). Bump version di `manifest.json`/`hacs.json` itu
  nice-to-have, BUKAN kewajiban tiap commit — cukup diinget pas mau bikin
  tag/release.
- Sebelum bikin tag rilis beneran, tanya dulu ke user apakah mau dibikinin
  catatan rilis dwibahasa (Indonesia + English), format siap paste ke
  `gh release create ... --notes`.
- Kalau ragu soal apapun yang nggak tercover di sini, TANYA ke user dulu,
  jangan asumsi sendiri — terutama soal keputusan yang berdampak ke entity
  lama (domain, unique_id format, dst).
