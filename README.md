# FortiClient EMS Docker Dashboards

Grafana, Prometheus and Loki monitoring for FortiClient EMS Docker deployments. Choose the configuration matching your EMS version.

| EMS deployment | Branch | Dashboards | Guide |
| --- | --- | --- | --- |
| 7.4.7 / PostgreSQL 15 | [ems-7.4](https://github.com/user01010111/FortiClientEMS-DockerDash/tree/ems-7.4) | 13 | [EMS 7.4 guide](https://forti.blog/guides/forticlient-ems-7-4-observability-guide) |
| 8.0.1.0192 / PostgreSQL 18 | [ems-8.0](https://github.com/user01010111/FortiClientEMS-DockerDash/tree/ems-8.0) | 16 | [EMS 8.0.1 guide](https://forti.blog/guides/forticlient-ems-8-0-1-observability-guide) |

The `main` branch keeps the original 7.4 configuration so existing checkouts continue to use the same files. The `ems-7.4` branch preserves that setup at revision `81b16d9`. New deployments should select a version explicitly.

## EMS 7.4

```bash
git clone --branch ems-7.4 https://github.com/user01010111/FortiClientEMS-DockerDash.git FortiClientEMS-DockerDash
```

Follow the [7.4 branch instructions](https://github.com/user01010111/FortiClientEMS-DockerDash/tree/ems-7.4#readme) or the [7.4 guide](https://forti.blog/guides/forticlient-ems-7-4-observability-guide).

## EMS 8.0

```bash
git clone --branch ems-8.0 https://github.com/user01010111/FortiClientEMS-DockerDash.git FortiClientEMS-DockerDash
```

The 8.0 branch targets **EMS 8.0.1.0192 with the bundled PostgreSQL 18 database**. It adds PostgreSQL Health, SQL Workload and DLP dashboards, collects statistics from both EMS databases, and preserves the updated nginx and fileserver routes.

Follow the [8.0 branch instructions](https://github.com/user01010111/FortiClientEMS-DockerDash/tree/ems-8.0#readme) or the [8.0.1 guide](https://forti.blog/guides/forticlient-ems-8-0-1-observability-guide).

## Existing installations

Keep local settings and credentials when updating. The branches contain different nginx templates, database collectors and SQL queries; select the branch after completing the matching EMS upgrade. Switching a Git branch does not upgrade EMS or migrate PostgreSQL data.

Both versions use a Compose override beside Fortinet's deployment files. Keep the existing Grafana, Prometheus and Loki volumes to retain dashboard settings, metrics and logs.
