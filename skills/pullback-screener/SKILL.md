---
name: pullback-screener
description: Trend içi geri çekilme (pullback) kurulumlarını tarar — 50SMA üstünde güçlü trenddeki hissede 10/21EMA'ya kontrollü geri çekilme + dönüş tetiği arar. Motor-yerleşik (strategy.evaluate_pullback); şu an DORMANT-değil, ARMED_SETUPS içinde ama R:R<2 planlar dürüstçe elenir.
---

# pullback-screener

Motor-yerleşik tarayıcı: `strategy.evaluate_pullback` her gün her hissede koşar; `screener_for("pullback")`
bu skill'e atfeder. Kayıt katmanına 2026-07-18 denetiminde eklendi (bulgu #35: armed bir setup'ın
tarayıcısı registry/pipeline/katalogda görünmezdi — atıf çalışıyordu ama Axis-2 önerileri kör kalıyordu).
