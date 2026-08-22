"""WP3/28d · CANLI spy.csv TAM ÇEKİM 2021+ (SALT-OKUMA; emsal exe007). Yerel/canlı bar
revizyon farkı ölçüldü (close_toplam 717318.68 vs 717320.57) — sınır günleri etiket
değiştirebilir; canlı-dünya rejim serisi canlı barlardan hesaplanacak. Yazma yok, emir yok."""
import json
import pandas as pd
spy = pd.read_csv("state/bars/spy.csv", parse_dates=["date"])
spy = spy[spy["date"] >= "2021-01-01"]
print(json.dumps({"satirlar": spy.assign(date=spy["date"].dt.strftime("%Y-%m-%d"))
                  .to_dict(orient="records")}))
