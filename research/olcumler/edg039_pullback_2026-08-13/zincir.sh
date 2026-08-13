#!/bin/zsh
# EDG-039 tam pencere zinciri — sıralı (8GB RAM: paralel replay swap riski)
cd /Users/erdemozturk/AI-Trading
D=research/olcumler/edg039_pullback_2026-08-13
.venv/bin/python $D/olcum.py eksipb > $D/kosum_eksipb.log 2>&1
echo "eksipb exit=$?" >> $D/zincir.log
.venv/bin/python $D/olcum.py taban  > $D/kosum_taban.log 2>&1
echo "taban exit=$?" >> $D/zincir.log
.venv/bin/python $D/olcum.py notrluk > $D/kosum_notrluk.log 2>&1
echo "notrluk exit=$?" >> $D/zincir.log
echo "ZINCIR BITTI" >> $D/zincir.log
