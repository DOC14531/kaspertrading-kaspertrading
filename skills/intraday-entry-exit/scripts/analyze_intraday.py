#!/usr/bin/env python3
"""
Analyse intraday : VWAP + bandes, Volume Profile, delta order flow (si dispo),
confluence Fibonacci, régime de marché (ATR), et stop suggéré.

Usage:
    python analyze_intraday.py chemin_vers_fichier.csv
    python analyze_intraday.py chemin_vers_fichier.json

Format CSV attendu (colonnes, ordre libre, insensible à la casse) :
    timestamp, open, high, low, close, volume
Colonnes optionnelles (pour le delta order flow) :
    buy_volume, sell_volume

Format JSON attendu (pour brancher directement la sortie de l'outil MCP
TradingView `data_get_ohlcv`) : une liste d'objets, ou un objet avec une clé
"bars"/"data" contenant cette liste. Chaque objet doit avoir open/high/low/
close/volume (insensible à la casse ; "time" ou "timestamp" acceptés,
optionnels — non utilisés dans les calculs). Colonnes optionnelles identiques
au CSV pour le delta order flow : buy_volume, sell_volume.

Si buy_volume/sell_volume absentes, le script utilise la tick rule
(approximation : hausse de close => volume classé acheteur, baisse => vendeur)
et le signale clairement comme une approximation, jamais comme une vraie mesure.
"""

import sys
import csv
import json
import statistics
from pathlib import Path


def _bar_from_dict(row):
    cols = {k.lower(): k for k in row}
    required = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in cols]
    if missing:
        raise ValueError(f"Champs manquants dans une barre: {missing}")
    bar = {
        "open": float(row[cols["open"]]),
        "high": float(row[cols["high"]]),
        "low": float(row[cols["low"]]),
        "close": float(row[cols["close"]]),
        "volume": float(row[cols["volume"]]),
    }
    has_delta = "buy_volume" in cols and "sell_volume" in cols
    if has_delta:
        bar["buy_volume"] = float(row[cols["buy_volume"]])
        bar["sell_volume"] = float(row[cols["sell_volume"]])
    return bar, has_delta


def load_bars_csv(path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        bars = []
        has_delta = False
        for row in reader:
            bar, row_has_delta = _bar_from_dict(row)
            has_delta = has_delta or row_has_delta
            bars.append(bar)
        return bars, has_delta


def load_bars_json(path):
    with open(path) as f:
        payload = json.load(f)
    if isinstance(payload, dict):
        for key in ("bars", "data", "result", "ohlcv"):
            if key in payload and isinstance(payload[key], list):
                payload = payload[key]
                break
    if not isinstance(payload, list):
        raise ValueError("JSON attendu: une liste de barres OHLCV (ou un objet contenant une clé 'bars'/'data')")
    bars = []
    has_delta = False
    for row in payload:
        bar, row_has_delta = _bar_from_dict(row)
        has_delta = has_delta or row_has_delta
        bars.append(bar)
    return bars, has_delta


def load_bars(path):
    path = Path(path)
    if path.suffix.lower() == ".json":
        return load_bars_json(path)
    return load_bars_csv(path)


def compute_vwap(bars):
    cum_pv = 0.0
    cum_v = 0.0
    vwap_series = []
    typical_prices = []
    for b in bars:
        tp = (b["high"] + b["low"] + b["close"]) / 3
        typical_prices.append(tp)
        cum_pv += tp * b["volume"]
        cum_v += b["volume"]
        vwap = cum_pv / cum_v if cum_v else tp
        vwap_series.append(vwap)
    final_vwap = vwap_series[-1]
    deviations = [tp - vwap for tp, vwap in zip(typical_prices, vwap_series)]
    stdev = statistics.pstdev(deviations) if len(deviations) > 1 else 0.0
    return {
        "vwap": final_vwap,
        "band_1sigma": (final_vwap - stdev, final_vwap + stdev),
        "band_2sigma": (final_vwap - 2 * stdev, final_vwap + 2 * stdev),
        "series": vwap_series,
    }


def compute_volume_profile(bars, n_buckets=20):
    lows = [b["low"] for b in bars]
    highs = [b["high"] for b in bars]
    price_min, price_max = min(lows), max(highs)
    if price_max == price_min:
        return None
    bucket_size = (price_max - price_min) / n_buckets
    buckets = [0.0] * n_buckets

    def bucket_index(price):
        idx = int((price - price_min) / bucket_size)
        return min(max(idx, 0), n_buckets - 1)

    for b in bars:
        mid = (b["high"] + b["low"]) / 2
        buckets[bucket_index(mid)] += b["volume"]

    total_volume = sum(buckets)
    poc_idx = buckets.index(max(buckets))
    poc_price = price_min + (poc_idx + 0.5) * bucket_size

    # Value area = 70% du volume autour du POC
    sorted_idx = sorted(range(n_buckets), key=lambda i: buckets[i], reverse=True)
    cum = 0.0
    included = set()
    for idx in sorted_idx:
        if cum >= 0.7 * total_volume:
            break
        included.add(idx)
        cum += buckets[idx]
    val_idx = min(included)
    vah_idx = max(included)
    return {
        "poc": poc_price,
        "val": price_min + val_idx * bucket_size,
        "vah": price_min + (vah_idx + 1) * bucket_size,
    }


def compute_delta(bars, has_real_data):
    total_buy = 0.0
    total_sell = 0.0
    for i, b in enumerate(bars):
        if has_real_data:
            total_buy += b["buy_volume"]
            total_sell += b["sell_volume"]
        else:
            if i == 0:
                continue
            if b["close"] > bars[i - 1]["close"]:
                total_buy += b["volume"]
            elif b["close"] < bars[i - 1]["close"]:
                total_sell += b["volume"]
            else:
                total_buy += b["volume"] / 2
                total_sell += b["volume"] / 2
    return {
        "delta": total_buy - total_sell,
        "buy_volume": total_buy,
        "sell_volume": total_sell,
        "is_approximation": not has_real_data,
    }


def compute_atr(bars, period=14):
    trs = []
    for i in range(1, len(bars)):
        h, l, prev_c = bars[i]["high"], bars[i]["low"], bars[i - 1]["close"]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
    if not trs:
        return 0.0
    window = trs[-period:] if len(trs) >= period else trs
    return sum(window) / len(window)


def compute_fib_levels(bars):
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    swing_high = max(highs)
    swing_low = min(lows)
    diff = swing_high - swing_low
    return {
        "swing_high": swing_high,
        "swing_low": swing_low,
        "38.2%": swing_high - 0.382 * diff,
        "50%": swing_high - 0.5 * diff,
        "61.8%": swing_high - 0.618 * diff,
    }


def find_confluence(vwap_data, vp_data, fib_data, tolerance_pct=0.15):
    levels = {"VWAP": vwap_data["vwap"]}
    if vp_data:
        levels["POC"] = vp_data["poc"]
        levels["VAH"] = vp_data["vah"]
        levels["VAL"] = vp_data["val"]
    for name, price in fib_data.items():
        if name in ("swing_high", "swing_low"):
            continue
        levels[f"Fib {name}"] = price

    names = list(levels.keys())
    confluences = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            p1, p2 = levels[names[i]], levels[names[j]]
            if p1 == 0:
                continue
            if abs(p1 - p2) / abs(p1) * 100 <= tolerance_pct:
                confluences.append((names[i], names[j], (p1 + p2) / 2))
    return confluences


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_intraday.py <fichier.csv>")
        sys.exit(1)

    path = Path(sys.argv[1])
    bars, has_real_delta_data = load_bars(path)

    vwap_data = compute_vwap(bars)
    vp_data = compute_volume_profile(bars)
    delta_data = compute_delta(bars, has_real_delta_data)
    atr = compute_atr(bars)
    fib_data = compute_fib_levels(bars)
    confluences = find_confluence(vwap_data, vp_data, fib_data)

    atr_pct = (atr / bars[-1]["close"] * 100) if bars[-1]["close"] else 0.0
    if atr_pct < 0.3:
        regime = "range serré"
    elif atr_pct > 1.0:
        regime = "tendanciel / forte volatilité"
    else:
        regime = "intermédiaire"

    print("=== RÉGIME DE MARCHÉ ===")
    print(f"ATR(14): {atr:.4f} ({atr_pct:.2f}% du prix) -> régime: {regime}")
    print("(Seuils en % du prix, donc valables aussi bien sur une action à 100$ qu'un BTC à 60000$,")
    print(" contrairement à un seuil ATR en valeur absolue qui n'a de sens que pour un seul actif.)")
    print()

    print("=== VWAP ===")
    print("(Calculé sur la fenêtre de barres fournie. Pour une action US: fournir uniquement")
    print(" la session RTH (9h30-16h00) pour un VWAP intraday classique. Pour un actif 24/7")
    print(" comme le BTC: fournir une fenêtre glissante cohérente (ex: 24h ou reset UTC 00:00),")
    print(" car il n'existe pas d'ouverture de séance unique à ancrer.)")
    print(f"VWAP: {vwap_data['vwap']:.4f}")
    print(f"Bande 1σ: {vwap_data['band_1sigma'][0]:.4f} / {vwap_data['band_1sigma'][1]:.4f}")
    print(f"Bande 2σ: {vwap_data['band_2sigma'][0]:.4f} / {vwap_data['band_2sigma'][1]:.4f}")
    print()

    if vp_data:
        print("=== VOLUME PROFILE ===")
        print(f"POC: {vp_data['poc']:.4f}")
        print(f"VAH: {vp_data['vah']:.4f} / VAL: {vp_data['val']:.4f}")
        print()

    print("=== FIBONACCI (swing complet de la période fournie) ===")
    print(f"Swing high: {fib_data['swing_high']:.4f} / Swing low: {fib_data['swing_low']:.4f}")
    print(f"38.2%: {fib_data['38.2%']:.4f} | 50%: {fib_data['50%']:.4f} | 61.8%: {fib_data['61.8%']:.4f}")
    print()

    print("=== DELTA ORDER FLOW ===")
    if delta_data["is_approximation"]:
        print("ATTENTION : buy_volume/sell_volume absents des données fournies.")
        print("Delta approximé via tick rule (close vs close précédent) — PAS une vraie mesure d'agresseur.")
    print(f"Delta: {delta_data['delta']:.2f} (buy: {delta_data['buy_volume']:.2f} / sell: {delta_data['sell_volume']:.2f})")
    print()

    print("=== ZONES DE CONFLUENCE (tolérance 0.15%) ===")
    if confluences:
        for a, b, price in confluences:
            print(f"{a} + {b} ≈ {price:.4f}")
    else:
        print("Aucune confluence détectée dans cette fenêtre — pas de signal de conviction élevée.")
    print()

    print("=== STOP SUGGÉRÉ ===")
    print(f"Stop = 1 à 1.5 x ATR(14) = {atr:.4f} à {atr * 1.5:.4f} (à appliquer depuis le prix d'entrée choisi)")


if __name__ == "__main__":
    main()
