

# Raspberry Pi 3 – Zabbix + SNMP Monitoring Lab
![Banner](docs/banner.png)
## 📌 Projekt áttekintése

Ez a labor projekt célja, hogy egy Raspberry Pi 3 segítségével gyakoroljuk a hálózati teljesítmény-monitorozást SNMP és Zabbix eszközökkel. A projekt egyszerre szolgál tanulási célokat és alapot adhat egy kisvállalati monitoring környezet szimulálására.

## ⚙️ Mit építettünk eddig

- Projektstruktúra létrehozása (`python/`, `docker/`, `web/`, `docs/`, `logs/`, `venv/`)
- Python virtualenv + függőségek telepítése (pysnmp, py-zabbix, requests)
- SNMP daemon (snmpd) telepítése és konfigurálása
- SNMP mini-dashboard script (uptime, load, memória, disk)
- Crontab ütemezés beállítása (5 percenkénti futtatás, log mentés)
- Next.js projekt létrehozása (TypeScript, Tailwind, App Router)
- Zabbix stack futtatása Mac-en Dockerben, Pi SNMP hostként való felvétele

## 📦 Követelmények

- **Raspberry Pi 3** – Raspberry Pi OS Bookworm (32-bit)
- **Python 3.11+** – python3-venv
- **SNMP** – snmpd, snmp (net-snmp)
- **Node.js** – NVM-mel telepítve javasolt
- **Docker Desktop** (Mac) – Zabbix stack futtatásához

## 🛠️ Telepítési útmutató

### 1) Python környezet (venv) + csomagok

A projekt külön virtuális környezetet (venv) használ, hogy elkerüljük a rendszer csomagjainak felülírását. A PEP 668 miatt ez kötelező.

```bash
cd ~/zabbix-labor
sudo apt install -y python3-venv
python3 -m venv venv
source venv/bin/activate
pip install pysnmp==4.4.12 pysmi==0.3.4 pyasn1==0.4.8 requests py-zabbix
pip freeze > requirements.txt
```

### 2) SNMP daemon telepítése és konfiguráció

Telepítés és engedélyezés:

```bash
sudo apt install -y snmpd snmp
sudo systemctl enable snmpd
sudo systemctl start snmpd
```

Konfiguráció (`/etc/snmp/snmpd.conf`):

```conf
view   all    included  .1
rocommunity public 127.0.0.1
rocommunity public 192.168.0.0/16  -V all
disk /
agentAddress udp:127.0.0.1:161,udp:161
```

Újraindítás a konfiguráció után:

```bash
sudo systemctl restart snmpd
```

### 3) Ellenőrzés SNMP-vel (numerikus OID)

```bash
# sysName.0
snmpget -v2c -c public 127.0.0.1 1.3.6.1.2.1.1.5.0

# Uptime
snmpget -v2c -c public 127.0.0.1 1.3.6.1.2.1.1.3.0

# Load 1 perc
snmpget -v2c -c public 127.0.0.1 1.3.6.1.4.1.2021.10.1.3.1

# Disk tábla
snmpwalk -v2c -c public 127.0.0.1 1.3.6.1.4.1.2021.9
```

### 4) Python „mini-dashboard"

A `snmp_overview.py` script a legfontosabb metrikákat írja ki (uptime, load, memória, disk).

Futtatás:

```bash
python python/snmp_overview.py 127.0.0.1 public
```

### 5) Ütemezett futtatás (cron)

Log mappa létrehozása:

```bash
mkdir -p ~/zabbix-labor/logs
```

Cron bejegyzés:

```bash
crontab -e
```

Adjuk hozzá a következő sort:

```cron
*/5 * * * * flock -n /home/pi/zabbix-labor/logs/snmp.lock bash -lc 'cd /home/pi/zabbix-labor && . venv/bin/activate && python python/snmp_overview.py 127.0.0.1 public >> /home/pi/zabbix-labor/logs/snmp_overview.log 2>&1'
```

### 6) Next.js projekt

A frontendhez Next.js 15 App Routert használtunk TypeScript, Tailwind és ESLint támogatással.

Létrehozás:

```bash
cd ~/zabbix-labor/web
npx create-next-app@latest .
```

Válaszok az interaktív promptra:
- TypeScript: ✔
- ESLint: ✔
- Tailwind CSS: ✔
- `src/` directory: ✔
- App Router: ✔
- Turbopack: ✔

### 7) Zabbix stack – Mac-en Dockerben

Mivel a Pi 3-on Debian 12 alatt a Zabbix 6.4/7.0 natív csomagjai nem teljesek, a Zabbix Server + Web + DB Mac-en, Docker Compose segítségével fut. A Pi SNMP hostként kerül felvételre a Zabbixba.

`docker-compose.yml` példa:

```yaml
services:
  db:
    image: mariadb:10.6
    environment:
      MARIADB_ROOT_PASSWORD: zabbix
      MARIADB_DATABASE: zabbix
      MARIADB_USER: zabbix
      MARIADB_PASSWORD: zabbix
    volumes:
      - dbdata:/var/lib/mysql
    restart: unless-stopped

  zabbix-server:
    image: zabbix/zabbix-server-mysql:alpine-7.0-latest
    environment:
      DB_SERVER_HOST: db
      MYSQL_USER: zabbix
      MYSQL_PASSWORD: zabbix
      MYSQL_DATABASE: zabbix
    ports:
      - "10051:10051"
    depends_on: [db]
    restart: unless-stopped

  zabbix-web:
    image: zabbix/zabbix-web-nginx-mysql:alpine-7.0-latest
    environment:
      DB_SERVER_HOST: db
      MYSQL_USER: zabbix
      MYSQL_PASSWORD: zabbix
      MYSQL_DATABASE: zabbix
      PHP_TZ: Europe/Budapest
      ZBX_SERVER_HOST: zabbix-server
    ports:
      - "8080:8080"
    depends_on: [db, zabbix-server]
    restart: unless-stopped

volumes:
  dbdata:
```

Stack indítása:

```bash
cd ~/zabbix-labor/docker
docker-compose up -d
```

A Zabbix web felület elérhető: `http://localhost:8080`

Alapértelmezett bejelentkezés:
- Username: `Admin`
- Password: `zabbix`

## 🚀 Következő lépések / Roadmap

- [ ] Zabbix API integráció Next.js-ben (hosts, triggers)
- [ ] Riasztások beállítása (pl. memória > 85%) és Telegram/webhook értesítés
- [ ] Dashboard oldalak frontend oldalon (Recharts/Chart.js)
- [ ] További SNMP metrikák: hálózati interfész forgalom, CPU-hőmérséklet (extend)

## 📁 Projektstruktúra

```
zabbix-labor/
├── python/          # Python scriptek (SNMP lekérdezések)
├── docker/          # Docker Compose fájlok
├── web/             # Next.js frontend
├── docs/            # Dokumentáció
├── logs/            # Log fájlok
└── venv/            # Python virtual environment
```

## 📝 Megjegyzések

- A projekt PEP 668 kompatibilis, minden Python csomag virtuális környezetben fut
- Az SNMP daemon csak a helyi hálózaton (192.168.0.0/16) és localhostról érhető el
- A Zabbix stack portjai: 8080 (web), 10051 (server)
- A cron job flock mechanizmust használ az átfedő futások elkerülésére

## 📄 Licenc

Ez egy oktatási/labor projekt.
