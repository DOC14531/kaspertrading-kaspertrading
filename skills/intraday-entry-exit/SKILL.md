---
name: intraday-entry-exit
description: "Calcule des points d'entrée et de sortie pour du day trading intraday sur actions US, en combinant VWAP + bandes d'écart-type, Volume Profile (POC/VAH/VAL), delta order flow (déséquilibre acheteur/vendeur) et retracements de Fibonacci en confluence. Utiliser ce skill dès que l'utilisateur mentionne day trading, intraday, scalping, entrée/sortie de position, VWAP, volume profile, order flow, order blocks, retracement, ou demande d'analyser une action US en cours de séance pour du trading court terme. Ne jamais se limiter à un seul indicateur, le skill exige une confluence d'au moins 2 signaux non-corrélés avant de proposer un niveau d'entrée ou de sortie."
---

# Intraday Entry/Exit — Day Trading Actions US

## Philosophie (lire avant d'utiliser)

Ce skill NE PEUT PAS produire de signal fiable à partir d'un seul indicateur. Un signal isolé (juste du Fibonacci, juste du RSI) est un piège à overfitting. Toute sortie de ce skill doit reposer sur une **confluence d'au moins 2 signaux non corrélés** parmi les 4 familles ci-dessous, plus un contexte de régime de marché (tendance vs range) et une règle de sortie basée sur la volatilité — jamais un pourcentage arbitraire.

Si l'utilisateur demande "donne-moi juste le Fibonacci" ou "juste du RSI", rappelle brièvement pourquoi ce n'est pas suffisant en confluence, mais fournis quand même l'info demandée à titre indicatif — jamais bloquer l'utilisateur, juste le prévenir.

## Étape 1 — Obtenir les données

Ce skill a besoin, pour le ticker et la séance demandés :
- Barres OHLCV intraday (1min ou 5min idéalement) pour VWAP et Volume Profile
- Idéalement bid/ask volume ou trades signés (aggressor side) pour le delta order flow — sans cette donnée, sauter cette famille de signal et le dire explicitement à l'utilisateur (ne jamais l'inventer)

Sources recommandées (voir `references/data-sources.md` pour le détail) :
- **Interactive Brokers TWS API** — L1/L2 gratuit avec compte financé, meilleure option si delta order flow est voulu
- **Polygon.io** — REST/WebSocket, bon fallback si pas de compte IBKR
- **Alpaca** — gratuit, correct pour prototyper VWAP + Volume Profile (attention : barres agrégées côté serveur, delta non fiable)

Si l'utilisateur colle directement des données (CSV, texte, capture), utiliser `scripts/analyze_intraday.py` sur le fichier fourni plutôt que de demander une source externe.

## Étape 2 — Calculer les 4 familles de signaux

Toutes les formules et seuils sont détaillés dans `references/methodology.md`. Résumé :

1. **VWAP + bandes d'écart-type (1σ/2σ)** — la référence d'exécution intraday. Prix au-dessus du VWAP = biais haussier intraday ; retour sur VWAP ou bande -1σ = zone d'entrée potentielle en tendance.
2. **Volume Profile (POC, VAH, VAL)** — les vrais niveaux de support/résistance, basés sur où le volume s'est réellement échangé, pas une ligne tracée à l'œil.
3. **Delta order flow** — déséquilibre acheteur/vendeur réel sur la zone testée (si donnée disponible). C'est la version rigoureuse de ce que le retail appelle "order blocks".
4. **Fibonacci retracement (38.2%, 50%, 61.8%)** — uniquement utilisé EN CONFLUENCE avec un des 3 signaux ci-dessus, jamais seul.

## Étape 3 — Générer le signal

Utiliser `scripts/analyze_intraday.py <fichier_csv>` qui calcule automatiquement les 4 familles et retourne :
- Le régime de marché du jour (tendance / range, via ATR)
- Les niveaux clés (VWAP, bandes, POC, VAH, VAL, niveaux Fib)
- Un score de confluence par zone de prix (jamais un signal binaire achète/vends)
- Un stop suggéré basé sur l'ATR (pas un pourcentage arbitraire)

## Étape 4 — Présenter le résultat à l'utilisateur

Toujours répondre avec :
- Le régime de marché actuel
- Les 2-3 zones de confluence les plus fortes (prix + signaux qui s'y superposent)
- Le stop suggéré (basé volatilité) et la taille de position implicite si le compte/risk % est connu
- Un rappel explicite si une famille de signal a été ignorée par manque de donnée (ex: pas de delta order flow disponible)

Ne jamais présenter un niveau d'entrée sans stop associé. Ne jamais recommander une taille de position sans connaître le risque max accepté par l'utilisateur (demander si inconnu).
