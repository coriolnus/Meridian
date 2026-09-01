"""v364 — ops/apisix_uygula.py tüketici + tüketici-grubu desteği (TSK-089 Faz 3-4).

NEDEN ÇİVİ: kimlikler (basic-auth panosu, key-auth botları, filo kota grubu) rotalarla AYNI
tek-kaynaktan (deploy/apisix/routes.yaml) inmezse Admin API'ye elle CRUD'la girer ve drift
denetiminin KÖR NOKTASI olur — "beyansız rota" yakalanırken "beyansız tüketici" yakalanmazdı.
Çivilenen dört şey:
  1. --uygula tüketici ve grup PUT'larını doğru URL + gövdeyle kurar (group_id taşınır),
  2. bölümler YOKKEN eski davranış aynen (geriye uyumluluk — rota-only yaml'lar kırılmaz),
  3. --denetle çıktısı tuketici_drift / grup_drift taşır ve aynı içerikte BOŞ, farkta DOLU,
  4. SIR: `$env://` referansı gövdeye ÇÖZÜLMEDEN, literal olarak gider.

GERÇEK AĞ ÇAĞRISI YOK: urlopen ve anahtar() monkeypatch'lenir; her istek bir kayda düşer.
`?ttl=` yasağı (kaynağı sessizce siler — TSK-089) kurulan URL'lerde ayrıca denetlenir.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from tests.conftest import betikten_modul_yukle  # noqa: E402

BETIK = KOK / "ops" / "apisix_uygula.py"

ROTA_YAML = """
rotalar:
  - id: r-bir
    uri: /bir
    plugins:
      prometheus: {}
"""

ROTA_UPSTREAM_YAML = """
rotalar:
  - id: r-upstream
    uri: /upstream
    plugins:
      prometheus: {}
    upstream:
      type: roundrobin
      nodes:
        "127.0.0.1:9000": 1
"""

TAM_YAML = ROTA_YAML + """
tuketici_gruplari:
  - id: filo
    plugins:
      limit-count:
        count: 1000
        time_window: 86400

tuketiciler:
  - username: bot_bekci
    group_id: filo
    plugins:
      key-auth:
        key: "$env://BOT_KEY_BEKCI"
  - username: pano_operator
    plugins:
      basic-auth:
        username: operator
        password: "$env://PANO_GIRIS_PAROLA"
"""


class SahteCevap:
    """urlopen'ın context-manager sözleşmesini taşıyan asgari sahte yanıt."""

    def __init__(self, govde: dict, status: int = 200):
        self.status = status
        self._ham = json.dumps(govde).encode()

    def read(self) -> bytes:
        return self._ham

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _liste(kalemler: list[dict]) -> dict:
    """Admin API'nin GET liste biçimi: {"list": [{"key": ..., "value": {...}}]}"""
    return {"list": [{"key": "/apisix/admin/x/" + str(k.get("id") or k.get("username")),
                      "value": k} for k in kalemler]}


@pytest.fixture()
def kur(monkeypatch, tmp_path):
    """Betiği yükler, ağı keser, çağrıları kaydeder. `yanitlar`: yol-öneki -> GET gövdesi."""
    mod = betikten_modul_yukle(BETIK, "apisix_uygula_v364")
    monkeypatch.setattr(mod, "anahtar", lambda: "SAHTE-ADMIN-ANAHTARI")

    cagrilar: list[dict] = []
    yanitlar: dict[str, dict] = {}

    def sahte_urlopen(req, timeout=None):
        yol = req.full_url[len(mod.BASE):]
        govde = json.loads(req.data.decode()) if req.data else None
        cagrilar.append({"method": req.get_method(), "yol": yol, "govde": govde,
                         "url": req.full_url})
        if req.get_method() == "GET":
            for onek, cevap in yanitlar.items():
                if yol.startswith(onek):
                    return SahteCevap(cevap)
            return SahteCevap({"list": []})
        return SahteCevap({}, status=200)

    monkeypatch.setattr(mod.urllib.request, "urlopen", sahte_urlopen)

    def yaml_yaz(metin: str):
        p = tmp_path / "routes.yaml"
        p.write_text(metin, encoding="utf-8")
        monkeypatch.setattr(mod, "ROTA_DOSYASI", p)
        return p

    return type("Kurulum", (), {"mod": mod, "cagrilar": cagrilar, "yanitlar": yanitlar,
                                "yaml_yaz": staticmethod(yaml_yaz)})


def _putlar(cagrilar: list[dict], onek: str) -> list[dict]:
    return [c for c in cagrilar if c["method"] == "PUT" and c["yol"].startswith(onek)]


# ---------------------------------------------------------------------------------------------
# 1. --uygula: tüketici + grup PUT'ları doğru URL ve gövdeyle kurulur
# ---------------------------------------------------------------------------------------------
def test_uygula_tuketici_ve_grup_putlari_kurar(kur):
    kur.yaml_yaz(TAM_YAML)
    rc = kur.mod.main(["--uygula"])
    assert rc == 0

    grup = _putlar(kur.cagrilar, "/consumer_groups/")
    assert [g["yol"] for g in grup] == ["/consumer_groups/filo"]
    assert grup[0]["govde"] == {"id": "filo", "plugins": {
        "limit-count": {"count": 1000, "time_window": 86400}}}

    tuk = _putlar(kur.cagrilar, "/consumers/")
    assert [t["yol"] for t in tuk] == ["/consumers/bot_bekci", "/consumers/pano_operator"]
    # group_id BEYAN EDİLDİĞİNDE taşınır, edilmediğinde gövdeye UYDURULMAZ.
    assert tuk[0]["govde"] == {"username": "bot_bekci", "group_id": "filo",
                               "plugins": {"key-auth": {"key": "$env://BOT_KEY_BEKCI"}}}
    assert "group_id" not in tuk[1]["govde"]

    # SIRA: rotalar → gruplar → tüketiciler (tüketici, dayandığı grup var olmadan PUT edilemez).
    yollar = [c["yol"] for c in kur.cagrilar if c["method"] == "PUT"]
    assert yollar.index("/routes/r-bir") < yollar.index("/consumer_groups/filo")
    assert yollar.index("/consumer_groups/filo") < yollar.index("/consumers/bot_bekci")

    # `?ttl=` HİÇBİR istekte olmaz (kaynağı sessizce siler — TSK-089).
    assert not [c for c in kur.cagrilar if "ttl" in c["url"]]


# ---------------------------------------------------------------------------------------------
# 2. Bölümler yokken eski davranış aynen (geriye uyumluluk)
# ---------------------------------------------------------------------------------------------
def test_bolumler_yokken_yalniz_rotalar(kur):
    kur.yaml_yaz(ROTA_YAML)
    rc = kur.mod.main(["--uygula"])
    assert rc == 0
    assert [c["yol"] for c in kur.cagrilar if c["method"] == "PUT"] == ["/routes/r-bir"]


def test_bolumler_yokken_denetle_alanlari_bos_ama_VAR(kur):
    """Alanlar şemadan DÜŞMEZ: okuyucu "bölüm yok" ile "alan yok"u ayırt edemezdi (Yasa 6)."""
    kur.yaml_yaz(ROTA_YAML)
    kur.yanitlar["/routes"] = _liste([{"id": "r-bir", "uri": "/bir",
                                       "plugins": {"prometheus": {}}}])
    rc, cikti = _denetle_calistir(kur)
    assert rc == 0
    assert cikti["drift"] == [] and cikti["tuketici_drift"] == [] and cikti["grup_drift"] == []


# ---------------------------------------------------------------------------------------------
# 3. --denetle: aynı içerik → boş drift; farklı içerik → dolu
# ---------------------------------------------------------------------------------------------
def _denetle_calistir(kur, capsys=None):
    import io
    import contextlib
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        rc = kur.mod.main(["--denetle"])
    return rc, json.loads(tampon.getvalue())


def test_denetle_ayni_icerik_bos_drift(kur):
    kur.yaml_yaz(TAM_YAML)
    kur.yanitlar["/routes"] = _liste([{"id": "r-bir", "uri": "/bir",
                                       "plugins": {"prometheus": {}}}])
    # Admin API create_time/update_time EKLER — normalize edilip düşülmezse drift SAHTE dolar.
    kur.yanitlar["/consumer_groups"] = _liste([
        {"id": "filo", "create_time": 111, "update_time": 222,
         "plugins": {"limit-count": {"count": 1000, "time_window": 86400}}}])
    kur.yanitlar["/consumers"] = _liste([
        {"username": "bot_bekci", "group_id": "filo", "create_time": 111, "update_time": 222,
         "plugins": {"key-auth": {"key": "$env://BOT_KEY_BEKCI"}}},
        {"username": "pano_operator", "create_time": 333,
         "plugins": {"basic-auth": {"username": "operator",
                                    "password": "$env://PANO_GIRIS_PAROLA"}}}])
    rc, cikti = _denetle_calistir(kur)
    assert cikti["tuketici_drift"] == []
    assert cikti["grup_drift"] == []
    assert cikti["drift"] == []
    assert rc == 0


def test_denetle_farkli_icerik_dolu_drift(kur):
    kur.yaml_yaz(TAM_YAML)
    kur.yanitlar["/routes"] = _liste([{"id": "r-bir", "uri": "/bir",
                                       "plugins": {"prometheus": {}}}])
    kur.yanitlar["/consumer_groups"] = _liste([
        {"id": "filo", "plugins": {"limit-count": {"count": 9, "time_window": 86400}}}])
    kur.yanitlar["/consumers"] = _liste([
        # bot_bekci EKSİK (etcd'de yok) + BEYANSIZ bir tüketici var (elle-CRUD sapması)
        {"username": "pano_operator",
         "plugins": {"basic-auth": {"username": "operator",
                                    "password": "$env://PANO_GIRIS_PAROLA"}}},
        {"username": "hayalet_elle", "plugins": {"key-auth": {"key": "x"}}}])
    rc, cikti = _denetle_calistir(kur)
    assert rc == 1
    assert any("bot_bekci" in s for s in cikti["tuketici_drift"])
    assert any("hayalet_elle" in s for s in cikti["tuketici_drift"])
    assert any("filo" in s for s in cikti["grup_drift"])


# ---------------------------------------------------------------------------------------------
# 4. SIR: $env:// çözülmeden, literal olarak gider
# ---------------------------------------------------------------------------------------------
def test_env_referansi_cozulmeden_gider(kur, monkeypatch):
    monkeypatch.setenv("BOT_KEY_BEKCI", "GERCEK-SIR-DEGERI")
    kur.yaml_yaz(TAM_YAML)
    kur.mod.main(["--uygula"])
    ham = json.dumps(kur.cagrilar, ensure_ascii=False)
    assert "$env://BOT_KEY_BEKCI" in ham
    assert "GERCEK-SIR-DEGERI" not in ham


# ---------------------------------------------------------------------------------------------
# 5. UPSTREAM (ölçülmüş hata): routes.yaml'daki `upstream` PUT gövdesine girmiyordu —
#    "missing upstream configuration in Route" 503'ü canlıda pano-ingress + fmp-veri'de üretti.
# ---------------------------------------------------------------------------------------------
def test_uygula_upstreamli_rota_govdesinde_upstream_birebir_var(kur):
    kur.yaml_yaz(ROTA_UPSTREAM_YAML)
    rc = kur.mod.main(["--uygula"])
    assert rc == 0
    putlar = _putlar(kur.cagrilar, "/routes/")
    assert putlar[0]["govde"] == {
        "uri": "/upstream", "plugins": {"prometheus": {}},
        "upstream": {"type": "roundrobin", "nodes": {"127.0.0.1:9000": 1}},
    }


def test_uygula_upstreamsiz_rota_govdesinde_upstream_anahtari_yok(kur):
    """Faz-1 ai-proxy rotaları upstream'siz — geriye uyumluluk: anahtar UYDURULMAZ."""
    kur.yaml_yaz(ROTA_YAML)
    rc = kur.mod.main(["--uygula"])
    assert rc == 0
    putlar = _putlar(kur.cagrilar, "/routes/")
    assert "upstream" not in putlar[0]["govde"]


def test_denetle_upstreamli_rota_fazladan_alanli_ayni_icerik_bos_drift(kur):
    """Admin API'nin upstream'e enjekte ettiği alanlar (hash_on/pass_host/scheme varsayılanı)
    BEYAN etmediğimiz için kıyastan düşer — yalnız beyan edilen anahtarlar (type+nodes) kıyaslanır.
    """
    kur.yaml_yaz(ROTA_UPSTREAM_YAML)
    kur.yanitlar["/routes"] = _liste([{
        "id": "r-upstream", "uri": "/upstream", "plugins": {"prometheus": {}},
        "upstream": {"type": "roundrobin", "nodes": {"127.0.0.1:9000": 1},
                     "hash_on": "vars", "pass_host": "pass", "scheme": "http"},
    }])
    rc, cikti = _denetle_calistir(kur)
    assert cikti["drift"] == []
    assert rc == 0


def test_denetle_upstreamli_rota_nodes_farkli_dolu_drift(kur):
    kur.yaml_yaz(ROTA_UPSTREAM_YAML)
    kur.yanitlar["/routes"] = _liste([{
        "id": "r-upstream", "uri": "/upstream", "plugins": {"prometheus": {}},
        "upstream": {"type": "roundrobin", "nodes": {"127.0.0.1:9999": 1},
                     "hash_on": "vars", "pass_host": "pass", "scheme": "http"},
    }])
    rc, cikti = _denetle_calistir(kur)
    assert rc == 1
    assert any("r-upstream" in s for s in cikti["drift"])


def test_gercek_routes_yaml_araci_sozlesmesine_uyar():
    """GERÇEK deploy/apisix/routes.yaml aracın beklediği şemayı taşır.

    Yukarıdaki çiviler sahte yaml'la konuşur — o yüzden araç ile TEK KAYNAK arasındaki
    sözleşmeyi ayrıca çivileriz: bölümler bir gün yeniden adlandırılsa (ya da bir tüketici
    `username`siz yazılsa) sahte-yaml çivileri yeşil kalır, dağıtım günü patlardı.
    Bu dosya BU testin okuduğu tek üretim artefaktıdır; test onu DEĞİŞTİRMEZ.
    """
    mod = betikten_modul_yukle(BETIK, "apisix_uygula_v364_gercek")
    assert [r["id"] for r in mod.rotalar()], "rotalar bölümü boş olamaz"
    for g in mod.tuketici_gruplari():
        assert g.get("id") and isinstance(g.get("plugins"), dict), f"grup şeması: {g}"
    for t in mod.tuketiciler():
        assert t.get("username") and isinstance(t.get("plugins"), dict), f"tüketici şeması: {t}"
        # group_id beyan edilmişse GERÇEK bir gruba işaret etmeli — yoksa PUT sırası anlamsız
        # ve APISIX tüketiciyi var olmayan gruba bağlayamaz.
        if t.get("group_id") is not None:
            assert t["group_id"] in {g["id"] for g in mod.tuketici_gruplari()}, \
                f"{t['username']} beyansız gruba bağlı: {t['group_id']}"


def test_kuru_kosum_yazmaz_ama_ne_yapacagini_soyler(kur, capsys):
    """Kuru koşum tüketicileri de ANLATIR — sessiz kalırsa operatör yalnız rotaları görürdü."""
    kur.yaml_yaz(TAM_YAML)
    rc = kur.mod.main([])
    assert rc == 0
    assert not [c for c in kur.cagrilar if c["method"] == "PUT"]
    cikti = capsys.readouterr().out
    assert "bot_bekci" in cikti and "filo" in cikti and "r-bir" in cikti
