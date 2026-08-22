"""BROKER ↔ KİTAP MUTABAKATI — "Alpaca'daki para panodakinden farklı" (2026-08-21).

OPERATÖR BİLDİRİMİ: *"alpacadaki toplam para ile panodaki tutar birbirinden farklı."*

ÖLÇÜLDÜ (canlı, 2026-08-21) ve şikâyet HAKLI çıktı — ama fark bir tek sayı değil, ÜÇ terimli
bir köprü ve sonunda AÇIKLANAMAYAN bir kalıntı var:

    broker equity (mark-to-market)      109.701,49
      − gerçekleşmemiş P&L                 −735,31
      = maliyet bazlı broker             108.966,18
      − broker'ın RESET GÜNÜ equity'si   −99.992,62   (2026-08-01, ölçüldü)
      = broker reset-sonrası kazanç        8.973,56
    kitap reset-sonrası kazanç             6.350,22   (= cash 106.350,22 − taban 100.000)
    ─────────────────────────────────────────────────
    AÇIKLANAMAYAN KALINTI                  2.623,34

Reset o gün iki tarafı MUTABIK kılmıştı (kitap 100.000 ↔ broker 99.992,62); ayrışma ondan
SONRA doğdu. Yani bu bir "tarihî fark" değil, YAŞAYAN bir kayıt eksiği.

NEDEN ÇİVİ: sistem ayrışmayı zaten biliyordu (`sermaye.durum()["ayrisik"] = True`) ama
KÖPRÜYÜ hiçbir yerde kurmuyordu — operatör iki sayı görüyor, aradaki terimleri göremiyordu.
Bir farkı BİLMEK ile onu AÇIKLAYABİLMEK aynı şey değildir; bu dosya ikincisini çivilir.

UYDURMA YASAĞI BURADA KRİTİK: köprünün her terimi ÖLÇÜLMÜŞ olmalı. Ölçülemeyen bir terim
(örn. broker geçmişi alınamadı) `None` + neden olarak durmalı ve kalıntıya KARIŞMAMALI —
aksi hâlde "açıklanamayan" sayısı bizim bilgisizliğimizi para farkı gibi gösterir.
"""
import inspect

from meridian import sermaye


def test_mutabakat_fonksiyonu_VAR():
    assert hasattr(sermaye, "broker_mutabakati"), (
        "broker↔kitap köprüsü yok — operatör iki sayıyı görüp aradaki terimleri göremez")


def test_kopru_TERIMLERI_ADIYLA_tasir():
    """Köprü bir tek sayı DEĞİL: her terim adıyla dursun ki hangi bacağın kaydığı görünsün."""
    fn = sermaye.broker_mutabakati
    src = inspect.getsource(fn)
    for terim in ("broker_equity", "gerceklesmemis_pnl", "broker_reset_gunu_equity",
                  "kitap_reset_sonrasi", "aciklanamayan"):
        assert terim in src, f"köprü `{terim}` terimini taşımıyor"


def test_olculemeyen_terim_KALINTIYA_KARISMAZ():
    """Bir terim ölçülemezse kalıntı UYDURULMAZ: `aciklanamayan` None olur ve neden yazılır.

    Aksi hâlde bizim bilgisizliğimiz (broker geçmişi alınamadı) bir PARA FARKI gibi okunur —
    ve o sayı operatörü yanlış yere baktırır."""
    out = sermaye.broker_mutabakati(
        broker_equity=None, gerceklesmemis_pnl=None,
        broker_reset_gunu_equity=None, kitap_cash=106350.22, sermaye_tabani=100000.0)
    assert out["aciklanamayan"] is None, f"ölçülemeyen terimle kalıntı uydurulmuş: {out}"
    assert out.get("olculemedi_neden"), "kalıntı None ama NEDEN yazılmamış (uydurma yasağı)"


def test_tam_olculdugunde_KALINTI_HESAPLANIR():
    """Bütün terimler ölçülüyse kalıntı SENTE kapanan bir çıkarma olmalı."""
    out = sermaye.broker_mutabakati(
        broker_equity=109701.49, gerceklesmemis_pnl=735.31,
        broker_reset_gunu_equity=99992.62, kitap_cash=106350.22, sermaye_tabani=100000.0)
    assert out["olculemedi_neden"] is None, out
    assert abs(out["broker_reset_sonrasi"] - 8973.56) < 0.01, out
    assert abs(out["kitap_reset_sonrasi"] - 6350.22) < 0.01, out
    assert abs(out["aciklanamayan"] - 2623.34) < 0.01, (
        f"kalıntı = broker_reset_sonrasi − kitap_reset_sonrasi olmalı: {out}")
