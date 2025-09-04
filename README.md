# 🔌 KiCad AI Interactive Chat

![KiCad AI Chat](logo.png)

> **Application multiplateforme interactive pour l'analyse de circuits électroniques KiCad avec IA**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/iyotee/Elektros)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🚀 Description

KiCad AI Interactive Chat est une application multiplateforme moderne qui combine l'analyse de circuits électroniques avec l'intelligence artificielle. L'application fonctionne sur Windows, macOS, Linux et même Raspberry Pi, permettant d'analyser automatiquement vos projets KiCad, d'enrichir les BOM avec des données API, et de discuter avec une IA spécialisée pour obtenir des insights et recommandations.

## ✨ Fonctionnalités Principales

### 🔍 Enrichissement Automatique des BOM
- **APIs Intégrées** : Octopart/Nexar et Mouser pour données complètes
- **Recherche Automatique** : Datasheets et modèles SPICE
- **Téléchargement Local** : Organisation automatique des fichiers

### 🛡️ Analyse SOA (Safe Operating Area)
- **Extraction PDF** : Reconnaissance automatique des limites de sécurité
- **Vérification Conformité** : Comparaison avec conditions d'exploitation
- **Alertes Temps Réel** : Notifications de violations potentielles

### 🤖 Chat IA Interactif
- **Questions Naturelles** : "Explique-moi la section d'alimentation"
- **Analyse Contextuelle** : Compréhension du circuit complet
- **Recommandations** : Suggestions d'amélioration spécifiques
- **Explications Pédagogiques** : Apprentissage des bonnes pratiques

### 📊 Simulation et Visualisation
- **Simulation SPICE** : Analyse AC/Bode automatique
- **Graphiques Interactifs** : Visualisation des résultats
- **Rapports Complets** : Export Markdown détaillé

## 🛠️ Installation

### Prérequis
- **Système d'exploitation** : Windows 10/11, macOS 10.15+, Linux (Ubuntu 18.04+)
- **Python 3.10+** ([Télécharger](https://python.org))
- **4GB RAM** minimum, 8GB recommandé
- **Connexion Internet** pour les APIs (optionnel)

### Installation Rapide

1. **Cloner le repository** :
   ```bash
   git clone https://github.com/iyotee/Elektros.git
   cd Elektros
   ```

2. **Installer les dépendances** :
   ```bash
   # Windows
   pip install -r requirements_web.txt
   
   # macOS/Linux
   pip3 install -r requirements_web.txt
   ```

3. **Lancer l'application** :
   ```bash
   # Windows
   python run_app.py
   
   # macOS/Linux
   python3 run_app.py
   ```

4. **Ouvrir dans le navigateur** : `http://localhost:8501`

### 🌐 Déploiement Web (Optionnel)

L'application peut être déployée sur le web :

#### **Streamlit Cloud (Gratuit)**
1. Fork ce repository
2. Connectez-vous à [share.streamlit.io](https://share.streamlit.io)
3. Déployez directement depuis GitHub

#### **Heroku (Gratuit)**
```bash
# Créer un Procfile
echo "web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0" > Procfile

# Déployer
git add Procfile
git commit -m "Add Procfile for Heroku"
git push heroku main
```

#### **Docker (Universel)**
```bash
# Créer un Dockerfile
FROM python:3.10-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements_web.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

## 🚀 Utilisation

### 1. Interface Principale
- **Upload de Fichiers** : Glissez-déposez vos fichiers KiCad
- **Analyse Automatique** : L'IA enrichit et analyse votre projet
- **Chat Interactif** : Posez des questions sur votre circuit

### 2. Fichiers Supportés
- **Netlist** : `.net`, `.xml` (KiCad)
- **BOM** : `.csv`, `.xml` (Bill of Materials)
- **Conditions** : `.yaml` (Operating Conditions)

### 3. Exemples de Questions
```
"Explique-moi la section d'alimentation"
"Y a-t-il des violations SOA ?"
"Comment optimiser le filtrage ?"
"Quel est le rôle du composant R1 ?"
"Suggestions pour améliorer la stabilité ?"
```

## 📁 Structure du Projet

```
Elektros/
├── app.py                    # Application Streamlit principale
├── run_app.py               # Script de lancement
├── kicad_ai_allinone.py    # Script de ligne de commande
├── requirements_web.txt     # Dépendances Python
├── web_config.yaml         # Configuration
├── logo.png                # Logo du projet
├── utils/                  # Modules utilitaires
│   ├── ai_analyzer.py      # Analyse IA
│   ├── api_clients.py      # Clients API
│   ├── soa_extractor.py    # Extraction SOA
│   └── spice_simulator.py  # Simulation SPICE
├── examples/               # Fichiers d'exemple
│   ├── sample_netlist.xml
│   ├── sample_bom.csv
│   └── operating_conditions.yaml
└── docs/                   # Documentation
    ├── API_REFERENCE.md
    └── USER_GUIDE.md
```

## 🔧 Configuration

### APIs Intégrées
L'application utilise automatiquement :
- **Nexar/Octopart** : Pour datasheets et modèles SPICE
- **Mouser** : Pour informations complémentaires

### Modèles IA
- **Par défaut** : `google/flan-t5-large` (CPU)
- **Avancé** : `mistralai/Mistral-7B-Instruct-v0.2` (GPU)

### Personnalisation
Modifiez `web_config.yaml` pour :
- Changer le modèle IA
- Ajuster les paramètres d'analyse
- Configurer les APIs
- Personnaliser l'interface

## 🖥️ Systèmes Supportés

### **Desktop**
- ✅ **Windows** 10/11 (x64, ARM64)
- ✅ **macOS** 10.15+ (Intel, Apple Silicon)
- ✅ **Linux** Ubuntu 18.04+, Debian, CentOS, Fedora
- ✅ **Raspberry Pi** OS (ARM64)

### **Cloud/Web**
- ✅ **Streamlit Cloud** (déploiement gratuit)
- ✅ **Heroku** (déploiement gratuit)
- ✅ **Railway** (déploiement gratuit)
- ✅ **Docker** (conteneurisation universelle)

### **Mobile/Tablet**
- ✅ **Accès web** depuis n'importe quel navigateur
- ✅ **Interface responsive** adaptée aux écrans tactiles

## 🎯 Cas d'Usage

### Pour les Ingénieurs Électroniques
- Vérification rapide de la sécurité des circuits
- Optimisation des designs existants
- Documentation automatique des projets

### Pour les Étudiants
- Compréhension des circuits complexes
- Apprentissage de l'analyse SOA
- Simulation interactive des circuits

### Pour les Équipes de Développement
- Review de code de circuits
- Standardisation des pratiques
- Formation des nouveaux membres

## 📊 Exemples d'Analyse

### Régulateur de Tension
1. **Upload** : `regulator.net` + `regulator_bom.csv`
2. **Analyse** : L'IA identifie la topologie et vérifie la stabilité
3. **Chat** : "Comment améliorer le rejet de bruit ?"

### Vérification SOA MOSFET
1. **Upload** : Circuit avec MOSFET de puissance
2. **Analyse** : Extraction des limites Vds, Id, Pd
3. **Vérification** : Comparaison avec conditions réelles
4. **Alertes** : Notifications si dépassement des limites

## 🚨 Dépannage

### Problèmes Courants

1. **Application ne démarre pas** :
   ```bash
   # Vérifier Python
   python --version
   
   # Réinstaller les dépendances
   pip install -r requirements_web.txt
   ```

2. **APIs ne fonctionnent pas** :
   - Vérifier la connexion internet
   - Les APIs sont optionnelles, l'application fonctionne sans

3. **Simulation échoue** :
   ```bash
   # Installer PySpice
   pip install PySpice
   ```

## 🤝 Contribution

### Développement
1. Fork du repository
2. Créer une branche feature
3. Implémenter les changements
4. Tester avec les exemples
5. Soumettre une pull request

### Tests
```bash
# Lancer l'application
python run_app.py

# Tester avec les exemples
# Utiliser les fichiers dans examples/
```

## 📄 Licence

MIT License - Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **KiCad** : Logiciel de conception électronique open-source
- **Streamlit** : Framework d'applications web Python
- **Hugging Face** : Plateforme de modèles IA
- **Octopart/Nexar** : API de composants électroniques
- **Mouser** : Distributeur de composants électroniques

## 📞 Support

- **Documentation** : Voir le dossier `docs/`
- **Issues** : [GitHub Issues](https://github.com/iyotee/Elektros/issues)
- **Discussions** : [GitHub Discussions](https://github.com/iyotee/Elektros/discussions)

---

**Développé avec ❤️ pour la communauté électronique**

*Version 1.0.0 - Janvier 2025*