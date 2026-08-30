"""EXE-2026-009 P-1 — İKİ SATIRIN DÜZELTİLMESİ (operatör hükmü 2026-08-29).

Bu, kartın kill#3'ünün ("geriye dönük pencere yeniden-etiketleme yapılırsa geçersiz") OPERATÖR
İSTİSNASIYLA aşıldığı tek seferlik bir düzeltmedir. Tam da bu yüzden betiğin cerrahi olduğu
KANITLANMAK zorunda: iki satır, ölçülmüş ön-koşullar, başka hiçbir satıra dokunma, idempotens.

ÖN-KOŞUL (ölçüldü, teshis_satirlar.json): hedef satırlar `motor="ayna"` · `karar="submitted"` ·
`plan_id ∈ {P-2026-08-21-DE, P-2026-08-21-PANW}` · `pencere="1345"` ·
`ts="2026-08-21T20:32:22+00:00"` — yani canlı barclock 1345'e dönmeden (2026-08-23T14:53:43Z)
İKİ GÜN ÖNCE, 13:30 rejiminde gönderilmişler.
"""
import pytest

from ops import pencere_damgasi_duzeltme_2026_08_29 as duz


def _hedef(plan_id, **ek):
    return {"date": "2026-08-21", "plan_id": plan_id, "ticker": plan_id.split("-")[-1],
            "motor": "ayna", "karar": "submitted", "pencere": "1345",
            "ts": "2026-08-21T20:32:22+00:00", "fill": 658.31, **ek}


def test_yalnizca_iki_hedef_satir_duzeltilir_digerleri_AYNEN_kalir():
    ic_satir = _hedef("P-2026-08-21-DE", motor="ic", karar="fill",
                      ts="2026-08-24T20:38:22+00:00", date="2026-08-24")
    baska_1345 = _hedef("P-2026-08-25-ECL", date="2026-08-25",
                        ts="2026-08-26T13:45:01+00:00")
    damgasiz = {"plan_id": "P-2026-08-05-NUE", "motor": "ayna", "karar": "submitted",
                "ts": "2026-08-05T22:10:00+00:00", "fill": 16.1}
    rows = [_hedef("P-2026-08-21-DE"), _hedef("P-2026-08-21-PANW"),
            ic_satir, baska_1345, damgasiz]
    onceki = [dict(r) for r in rows]

    yeni, rapor = duz.duzelt(rows)

    assert [r["pencere"] for r in yeni[:2]] == ["1330", "1330"]
    assert rapor["duzeltilen"] == 2
    # ic satırı, gerçek 1345 satırı ve damgasız satır TEK ALAN değişmeden kalır
    assert yeni[2:] == onceki[2:]
    # düzeltme sessiz değil: satır kendi gerekçesini taşır (denetim izi)
    assert "1330" in yeni[0]["pencere_duzeltme"] or yeni[0]["pencere_duzeltme"]


def test_ts_beklenenle_uyusmazsa_HICBIR_SATIRA_dokunulmaz():
    """Ön-koşul tutmuyorsa betik yarım iş bırakmaz — hiç yazmaz."""
    rows = [_hedef("P-2026-08-21-DE"),
            _hedef("P-2026-08-21-PANW", ts="2026-08-24T13:45:00+00:00")]  # beklenmeyen ts
    onceki = [dict(r) for r in rows]
    with pytest.raises(duz.OnKosulHatasi):
        duz.duzelt(rows)
    assert rows == onceki


def test_ikinci_kosum_idempotent():
    rows = [_hedef("P-2026-08-21-DE"), _hedef("P-2026-08-21-PANW")]
    yeni, _ = duz.duzelt(rows)
    yeni2, rapor2 = duz.duzelt(yeni)
    assert yeni2 == yeni
    assert rapor2["duzeltilen"] == 0
    assert rapor2["zaten_duzeltilmis"] == 2


def test_hedef_satir_bulunamazsa_SESSIZ_gecmez():
    """Defterde hedef yoksa bu bir başarı değil, bir uyuşmazlıktır (yanlış makine/yanlış defter)."""
    with pytest.raises(duz.OnKosulHatasi):
        duz.duzelt([{"plan_id": "P-BASKA", "motor": "ayna", "karar": "submitted"}])
