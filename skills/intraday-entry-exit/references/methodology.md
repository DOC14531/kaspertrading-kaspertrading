# Méthodologie de calcul

## 1. VWAP + bandes d'écart-type
- VWAP = somme(prix_typique × volume) / somme(volume), cumulé depuis l'ouverture de séance
- prix_typique = (high + low + close) / 3
- Bandes = VWAP ± k × écart-type des écarts (prix_typique - VWAP), k = 1 et 2
- Usage : en tendance, un retour sur VWAP ou bande -1σ (long) / +1σ (short) est une
  zone d'entrée ; une cassure de la bande 2σ signale un excès à faire fader ou à éviter

## 2. Volume Profile
- Découper la fourchette de prix de la séance en buckets (ex: 0.05$ ou selon tick size)
- Sommer le volume échangé dans chaque bucket
- POC (Point of Control) = bucket avec le plus de volume
- Value Area (70% du volume) = VAH (borne haute) / VAL (borne basse)
- Usage : POC agit comme aimant de prix ; VAH/VAL sont des niveaux de retournement
  probables si le prix revient dessus avec perte de momentum

## 3. Delta order flow
- Delta = volume acheteur agressif - volume vendeur agressif sur une bougie ou une zone
- Nécessite les trades signés (aggressor side) ou approximation par tick rule si non fourni
- Usage : un delta fortement positif sur un test de support = absorption acheteuse
  réelle (équivalent rigoureux d'un "order block" haussier)
- Si la donnée n'est pas disponible, NE PAS approximer silencieusement — le signaler

## 4. Fibonacci retracement
- Sur la dernière impulsion identifiée (swing high → swing low ou inverse)
- Niveaux : 38.2%, 50%, 61.8%
- Usage : uniquement comme confirmation si un niveau Fib coïncide avec un POC/VAH/VAL
  ou une bande VWAP — jamais utilisé isolément comme signal

## Régime de marché (filtre obligatoire avant tout signal)
- ATR(14) sur les barres du jour comparé à sa moyenne des 5 derniers jours
- Range étroit + prix oscillant autour du VWAP = régime range → privilégier les fades
  aux extrêmes de Value Area
- ATR élevé + prix qui s'éloigne du VWAP avec volume croissant = régime tendance →
  privilégier les retours sur VWAP/bande -1σ dans le sens de la tendance

## Stop et sizing
- Stop = k × ATR(14), jamais un pourcentage fixe arbitraire (k typique : 1 à 1.5)
- Taille de position = (capital × risque max en %) / (distance stop en $)
- Si le risque max par trade n'est pas connu, le demander avant de suggérer une taille
