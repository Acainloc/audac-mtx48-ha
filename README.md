# AUDAC MTX – Home Assistant (HACS)

Contrôlez votre AUDAC MTX48/MTX88 via TCP/IP (port 5001) : volume, mute, source par zone.

## Installation
1. Ajoutez ce dépôt dans HACS > Custom repositories (Category: Integration).
2. Installez **AUDAC MTX** depuis HACS.
3. Redémarrez Home Assistant.
4. Ajoutez l'intégration **AUDAC MTX** via Paramètres > Appareils & services.

## Options
- `poll_interval` (par défaut 5 s) : intervalle de mise à jour.
- `rate_limit_ms` (par défaut 120 ms) : délai minimal entre deux commandes.

## Services
- `audac_mtx.save_preset` — `{"name": "soirée"}`
- `audac_mtx.load_preset` — `{"name": "soirée"}`

## Notes
- La matrice n’accepte qu’une connexion TCP à la fois.
- Test rapide: `printf "#|M001|F001|SV01|60|U|\r\n" | nc <IP> 5001`
