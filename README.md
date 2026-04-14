# FortiClient EMS Docker Dashboards

Extends a containerised **FortiClient EMS v7.4.x** deployment with a fuller Grafana + Prometheus observability layer — without modifying Fortinet's files.

## What this adds

| Component | Change |
|---|---|
| **Grafana** | Exposes the bundled Grafana instance at `https://<fqdn>/grafana/` via nginx |
| **PostgreSQL datasources** | Fixes the broken `fcm` and `fcm_default` datasources with correct env vars |
| **Prometheus layer** | Adds Prometheus, node-exporter, cAdvisor, nginx/Postgres/Redis/PgBouncer/Consul exporters, and blackbox probes |
| **Dashboards** | 13 provisioned dashboards: 3 EMS views plus 10 stack, host, datastore, control-plane, and inventory views |
| **nginx** | Adds `/grafana/` reverse proxy location and internal-only `stub_status` for Prometheus scraping |

Everything layers on top of Fortinet's existing containers via `docker-compose.override.yml`.

## Screenshot Gallery

Representative screenshots from the working stack are included under [`docs/screenshots/`](docs/screenshots/). Log-heavy views are intentionally omitted or redacted where they would otherwise expose request details or client addresses.

<details>
<summary>View dashboard screenshots</summary>

### EMS views

![EMS Fleet Overview](docs/screenshots/ems-fleet-overview.png)
![EMS Security Posture](docs/screenshots/ems-security-posture.png)
![EMS Policies & ZTNA](docs/screenshots/ems-policies-ztna.png)
![EMS Admin & Licensing](docs/screenshots/ems-admin-licensing.png)

### Platform views

![EMS Stack Overview](docs/screenshots/ems-stack-overview.png)
![EMS Host Health](docs/screenshots/ems-host-health.png)
![EMS Datastores](docs/screenshots/ems-datastores.png)
![EMS Containers](docs/screenshots/ems-containers.png)

### Control plane views

![EMS Control Plane](docs/screenshots/ems-control-plane.png)
![EMS Reverse Proxy](docs/screenshots/ems-reverse-proxy.png)

</details>

## Vanilla EMS Service Maps

These diagrams describe the stock FortiClient EMS Docker deployment, not the extra observability services added by this project. They are based on the vanilla `docker-compose.yaml` service names, published ports, and declared `depends_on` relationships.

<details>
<summary>1. Vanilla service map</summary>

```mermaid
flowchart TD
  subgraph Edge["Published entry points"]
    nginx["nginx
80, 443, 10443"]
    fos["fos
8015, 50000"]
    ecsocksrv["ecsocksrv
8013"]
    adevtsrv["adevtsrv
8871"]
    scep["scep
4001, 4002"]
    chromebook["chromebook
8443"]
  end

  subgraph Platform["Core platform"]
    db["db"]
    redis["redis"]
    consul["consul"]
    deploy["deploy"]
    pgbouncer["pgbouncer"]
    ws_pgbouncer["ws_pgbouncer"]
    das["das"]
    dbop["dbop"]
    daemons["daemons"]
    webserver["webserver"]
    monitor["monitor"]
    adconnector["adconnector"]
    ztna["ztna"]
    mdmproxy["mdmproxy"]
  end

  subgraph Workers["Worker services"]
    probe["probe"]
    reg["reg"]
    tag["tag"]
    ka["ka"]
    upload["upload"]
    event["event"]
    forensics["forensics"]
  end

  subgraph BuiltInObs["Bundled observability"]
    promtail["promtail"]
    loki["loki"]
    grafana["grafana"]
  end

  db --> pgbouncer
  db --> ws_pgbouncer
  db --> consul
  db --> redis
  deploy --> redis

  db --> das
  redis --> das

  das --> fos
  db --> fos

  db --> ecsocksrv
  consul --> ecsocksrv
  fos --> ecsocksrv

  db --> adevtsrv
  fos --> adevtsrv
  consul --> adevtsrv
  redis --> adevtsrv

  db --> probe
  das --> probe
  fos --> probe
  consul --> probe
  redis --> probe

  db --> reg
  das --> reg
  fos --> reg
  consul --> reg
  redis --> reg

  db --> tag
  das --> tag
  fos --> tag
  consul --> tag
  redis --> tag

  db --> ka
  das --> ka
  fos --> ka
  consul --> ka
  redis --> ka

  db --> upload
  das --> upload
  fos --> upload
  consul --> upload
  redis --> upload

  db --> event
  das --> event
  fos --> event
  consul --> event
  redis --> event

  db --> forensics
  das --> forensics
  fos --> forensics
  consul --> forensics
  redis --> forensics

  db --> dbop
  das --> dbop
  fos --> dbop
  consul --> dbop
  redis --> dbop

  db --> ztna
  das --> ztna
  redis --> ztna

  promtail --> mdmproxy
  pgbouncer --> mdmproxy
  nginx --> mdmproxy
  webserver --> mdmproxy

  pgbouncer --> scep
  nginx --> scep
  webserver --> scep
  mdmproxy --> scep

  das --> chromebook

  ztna --> nginx

  db --> daemons
  das --> daemons
  redis --> daemons
  fos --> daemons

  das --> monitor
  redis --> monitor

  db --> adconnector
  das --> adconnector
  redis --> adconnector

  loki --> promtail
```

</details>

<details>
<summary>2. Published ports in the vanilla deployment</summary>

```mermaid
flowchart LR
  Internet["Clients / Internet"]

  subgraph EMS["Vanilla EMS published services"]
    nginx["nginx
80, 443, 10443"]
    fos["fos
8015, 50000"]
    ecsocksrv["ecsocksrv
8013"]
    adevtsrv["adevtsrv
8871"]
    scep["scep
4001, 4002"]
    chromebook["chromebook
8443"]
  end

  Internet --> nginx
  Internet --> fos
  Internet --> ecsocksrv
  Internet --> adevtsrv
  Internet --> scep
  Internet --> chromebook
```

</details>

<details>
<summary>3. Operator-friendly view</summary>

```mermaid
flowchart TB
  subgraph Public["Public-facing edge"]
    PublicWeb["Public web entry
(nginx)"]
    FOS["Core EMS network service
(fos)"]
    ECSock["Endpoint socket service
(ecsocksrv)"]
    ADEvents["AD event listener
(adevtsrv)"]
    SCEP["Certificate enrollment service
(scep)"]
    Chromebook["Chromebook service
(chromebook)"]
  end

  subgraph App["Application and control plane"]
    WebUI["EMS web application
(webserver)"]
    Bootstrap["Deployment/bootstrap
(deploy)"]
    DAS["Core backend service
(das)"]
    DBOP["Database operations
(dbop)"]
    Daemons["Shared background daemons
(daemons)"]
    Monitor["Monitoring worker
(monitor)"]
    ADConnector["Active Directory connector
(adconnector)"]
    ZTNA["ZTNA service
(ztna)"]
    MDM["MDM proxy
(mdmproxy)"]
  end

  subgraph Data["Data and coordination"]
    Postgres["PostgreSQL
(db)"]
    PgBouncer["PgBouncer
(pgbouncer)"]
    WsPgBouncer["Webserver PgBouncer
(ws_pgbouncer)"]
    Redis["Redis cache / queue
(redis)"]
    Consul["Service coordination
(consul)"]
  end

  subgraph Workers["Background workers"]
    Probe["Probe worker
(probe)"]
    Register["Register worker
(reg)"]
    Tag["Tag worker
(tag)"]
    KeepAlive["Keepalive worker
(ka)"]
    Upload["Upload worker
(upload)"]
    Event["Event worker
(event)"]
    Forensics["Forensics worker
(forensics)"]
  end

  subgraph Logs["Bundled logging and dashboards"]
    Promtail["Promtail"]
    Loki["Loki"]
    Grafana["Grafana"]
  end

  PublicWeb --> WebUI
  PublicWeb --> MDM
  PublicWeb --> SCEP
  PublicWeb --> ZTNA

  Bootstrap --> Redis
  Postgres --> PgBouncer
  Postgres --> WsPgBouncer
  Postgres --> DAS
  Postgres --> DBOP
  Postgres --> Daemons
  Postgres --> ADConnector

  Redis --> DAS
  Redis --> Daemons
  Redis --> Monitor
  Redis --> ADConnector
  Redis --> ZTNA

  DAS --> FOS
  DAS --> Probe
  DAS --> Register
  DAS --> Tag
  DAS --> KeepAlive
  DAS --> Upload
  DAS --> Event
  DAS --> Forensics
  DAS --> Chromebook

  Consul --> Probe
  Consul --> Register
  Consul --> Tag
  Consul --> KeepAlive
  Consul --> Upload
  Consul --> Event
  Consul --> Forensics

  Loki --> Promtail
```

</details>

## Prerequisites

- FortiClient EMS v7.4.7+ running via Docker Compose (the three observability containers — `promtail`, `loki`, `grafana` — must be healthy)
- `git` available on the EMS host
- Access to the EMS host as a user with `sudo` and Docker access

## Quick Start

### 1. Clone this repo onto the EMS host

```bash
cd /home/<user>
git clone <repo-url> FortiClientEMS-DockerDash
```

### 2. Add env vars to `.env`

The `.env` file lives alongside `docker-compose.yaml`. Append two lines:

```bash
echo 'FQDN=<your-ems-fqdn>'           >> /home/<user>/.env
echo 'GF_ADMIN_PASSWORD=<strong-pw>'  >> /home/<user>/.env
```

`POSTGRES_PASSWORD` is already present from the EMS install — do not change it.

### 3. Symlink the override into the compose project root

```bash
ln -s /home/<user>/FortiClientEMS-DockerDash/docker-compose.override.yml \
      /home/<user>/docker-compose.override.yml
```

### 4. Syntax-check the nginx config before applying

```bash
docker run --rm \
  -v /home/<user>/FortiClientEMS-DockerDash/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
  nginx:alpine nginx -t
```

Expected output: `nginx: configuration file /etc/nginx/nginx.conf syntax is ok`

### 5. Validate the merged compose config

```bash
cd /home/<user>
docker compose config | grep -A 30 '  grafana:'
```

Confirm the `EMS_DB_HOST`, `GF_SERVER_ROOT_URL`, and volume mounts appear.

### 6. Start the observability services

```bash
cd /home/<user>
docker compose up -d --no-deps \
  grafana nginx prometheus node-exporter cadvisor \
  nginx-prometheus-exporter postgres-exporter redis-exporter \
  pgbouncer-exporter consul-exporter blackbox-exporter
```

`--no-deps` prevents Docker Compose from cascading restarts to unrelated EMS services.

### 7. Open Grafana

Navigate to `https://<your-fqdn>/grafana/` — you should reach the Grafana login page.  
Login: `admin` / `<GF_ADMIN_PASSWORD>`

## Verification

```bash
cd /home/<user>

# Check datasource health (Prometheus)
docker compose exec -T grafana \
  wget -qO- \
  --post-data='' \
  "http://admin:${GF_ADMIN_PASSWORD}@localhost:3000/grafana/api/datasources/uid/ems-prometheus/health"
# Expected: {"status":"OK",...}

# Check datasource health (PostgreSQL)
docker compose exec -T grafana \
  wget -qO- \
  --post-data='' \
  "http://admin:${GF_ADMIN_PASSWORD}@localhost:3000/grafana/api/datasources/uid/ems-fcm-default/health"
# Expected: {"status":"OK",...}

# Check Loki datasource
docker compose exec -T grafana \
  wget -qO- \
  --post-data='' \
  "http://admin:${GF_ADMIN_PASSWORD}@localhost:3000/grafana/api/datasources/uid/ems-loki/health"
# Expected: {"status":"OK"}

# Confirm dashboards are provisioned (expect 13 results)
docker compose exec -T grafana \
  wget -qO- "http://admin:${GF_ADMIN_PASSWORD}@localhost:3000/grafana/api/search?type=dash-db" \
  | python3 -m json.tool | grep '"title"'

# Confirm Prometheus targets are healthy
docker compose exec -T prometheus \
  wget -qO- "http://localhost:9090/api/v1/targets" | python3 -m json.tool
```

## Upgrading EMS

When Fortinet releases a new EMS version:

1. Follow Fortinet's upgrade procedure (this will update `docker-compose.yaml` and the container images).
2. Re-extract the nginx config from the new image:
   ```bash
   docker cp "$(docker compose ps -q nginx)":/etc/nginx/nginx.conf \
     /home/<user>/FortiClientEMS-DockerDash/nginx/nginx.conf.new
   diff nginx/nginx.conf nginx/nginx.conf.new
   ```
3. Re-apply the Grafana location blocks (search for `── Grafana` in [nginx/nginx.conf](nginx/nginx.conf)).
4. Run `docker compose up -d --no-deps grafana nginx` again.

The `docker-compose.override.yml` and dashboard JSON files require no changes on upgrade unless Fortinet changes the container internals.

## File Structure

```
FortiClientEMS-DockerDash/
├── docker-compose.override.yml           # Merged with Fortinet's compose file
├── .env.example                          # Template — copy to .env, never commit .env
├── docs/
│   └── screenshots/                      # Sanitised example dashboard screenshots
├── nginx/
│   └── nginx.conf                        # EMS nginx config + Grafana proxy locations
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   ├── loki.yml                  # Loki + fcm + fcm_default datasources
│   │   │   ├── metrics.yml               # Prometheus datasource
│   │   └── dashboards/
│   │       └── dashboards.yml            # File provider config
│   └── dashboards/
│       ├── ems-fleet-overview.json       # Endpoint counts, OS, version spread
│       ├── security-posture.json         # AV coverage, vulnerabilities, events
│       └── service-logs.json             # Loki log streams and error rates
├── prometheus/
│   ├── blackbox.yml                      # Blackbox probe modules
│   ├── entrypoint.sh                     # Renders Prometheus config with Grafana auth
│   └── prometheus.yml.tmpl               # Scrape jobs for stack, host, DB, probes
```

## Hardening (recommended follow-up)

Create a read-only PostgreSQL role for Grafana rather than using the `postgres` superuser:

```sql
CREATE ROLE grafana_reader LOGIN PASSWORD '<password>';
GRANT CONNECT ON DATABASE fcm_default TO grafana_reader;
GRANT USAGE ON SCHEMA public TO grafana_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO grafana_reader;
-- Repeat for fcm database
GRANT CONNECT ON DATABASE fcm TO grafana_reader;
```

Then update `EMS_DB_USER` and `EMS_DB_PASSWORD` in `.env` and `docker compose up -d --no-deps grafana`.
