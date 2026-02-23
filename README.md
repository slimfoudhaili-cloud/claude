# Outlook Calendar - Python

Accédez à votre calendrier Outlook depuis un script Python via **Microsoft Graph API**.

---

## Prérequis

1. **Python 3.8+**
2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration Azure (1 fois)

Vous avez besoin d'un **Client ID** Azure pour authentifier l'application.

### Étapes

1. Rendez-vous sur [portal.azure.com](https://portal.azure.com)
2. **Azure Active Directory** → **App registrations** → **New registration**
3. Nom : `Outlook Calendar Python` (ou autre)
4. Supported account types : `Personal Microsoft accounts only` (ou `Any Azure AD directory`)
5. Cliquez **Register**
6. Copiez l'**Application (client) ID**

### Ajouter les permissions

1. Dans votre app → **API permissions** → **Add a permission**
2. **Microsoft Graph** → **Delegated permissions**
3. Ajouter : `Calendars.ReadWrite`, `User.Read`
4. Cliquer **Grant admin consent** (si vous êtes admin) ou continuer sans

---

## Utilisation

### Option 1 — Variable d'environnement (recommandé)

```bash
export AZURE_CLIENT_ID="votre-client-id-ici"
python outlook_calendar.py
```

### Option 2 — Modifier le script

Ouvrez `outlook_calendar.py` et remplacez :
```python
CLIENT_ID = "YOUR_CLIENT_ID_HERE"
```
par votre Client ID.

---

## Première connexion

Au premier lancement, un **code** s'affiche dans le terminal :

```
==============================
AUTHENTICATION REQUIRED
==============================
1. Open: https://microsoft.com/devicelogin
2. Enter code: ABCD1234
==============================
```

1. Ouvrez le lien dans votre navigateur
2. Entrez le code affiché
3. Connectez-vous avec votre compte Microsoft/Outlook

Le token est ensuite sauvegardé localement dans `.outlook_token_cache.json` — vous n'aurez plus à vous reconnecter.

---

## Fonctionnalités

| Option | Description |
|--------|-------------|
| 1 | Voir les événements des 7 prochains jours |
| 2 | Voir les événements des 30 prochains jours |
| 3 | Créer un nouvel événement |
