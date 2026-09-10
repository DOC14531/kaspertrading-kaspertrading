# Sources de données recommandées

## Interactive Brokers TWS API (priorité 1)
- https://interactivebrokers.github.io/tws-api/
- L1 + L2 (carnet d'ordres) inclus gratuitement avec un compte financé
- Permet aussi l'exécution directe une fois la stratégie validée
- Nécessite TWS ou IB Gateway lancé localement pour l'API

## Polygon.io (priorité 2 / fallback sans compte broker)
- https://polygon.io
- Plan Developer (79$/mois) : WebSocket temps réel, tick-level
- Plan Advanced (199$/mois) : historique tick complet
- Bon choix si tu veux rester en pur API sans gérer un compte broker

## Alpaca (prototypage gratuit)
- https://alpaca.markets
- API gratuite, données IEX temps réel ou SIP selon le plan
- Attention : agrégation des barres côté serveur — le delta order flow calculé
  dessus n'est pas fiable, seulement VWAP/Volume Profile sur barres 1-5min

## Databento (si microstructure avancée nécessaire)
- https://databento.com
- Order book complet, qualité institutionnelle, plus cher
- Utile seulement si la stratégie exploite vraiment la profondeur de marché

## À éviter pour ce skill
- Alpha Vantage / Finnhub gratuits : limites de taux trop basses pour un usage
  intraday systématique (25 appels/jour pour Alpha Vantage)
