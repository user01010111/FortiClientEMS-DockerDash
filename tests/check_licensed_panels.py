#!/usr/bin/env python3
"""Exercise empty/populated dashboard branches in TEMP tables on the real EMS schema.

Requires Docker access to PostgreSQL 18. Explicit IDs avoid consuming vendor sequences.
All fixtures are session-local and the transaction is rolled back, including on failure.
"""
import argparse
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def target(file, title):
    dashboard = json.loads((ROOT / 'grafana/dashboards' / file).read_text())
    panel = next(p for p in dashboard['panels'] if p['title'] == title)
    return panel['targets'][0]['rawSql'].strip().rstrip(';')


def check(container, database, tables, inserts, cases):
    parts = ["BEGIN; SET LOCAL TIME ZONE 'UTC';"]
    parts += [f'CREATE TEMP TABLE {name} (LIKE public.{name} INCLUDING DEFAULTS);' for name in tables]
    expected = {}
    for phase in ['empty', 'populated']:
        if phase == 'populated':
            parts.append(inserts)
        for i, (file, title, empty, populated) in enumerate(cases):
            key = phase + str(i)
            expected[key] = empty if phase == 'empty' else populated
            parts.append("SELECT '" + key + "=' || coalesce(json_agg(row_to_json(q)),'[]'::json)::text FROM (" + target(file, title) + ') q;')
    parts.append('ROLLBACK;')
    result = subprocess.run(['docker', 'exec', '-i', '-u', 'postgres', container, 'psql', '-X', '-At',
                             '-v', 'ON_ERROR_STOP=1', '-d', database], input='\n'.join(parts),
                            text=True, capture_output=True, check=True)
    actual = {line.split('=', 1)[0]: json.loads(line.split('=', 1)[1])
              for line in result.stdout.splitlines() if '=' in line and line.split('=', 1)[0] in expected}
    assert actual.keys() == expected.keys()
    for key, rows in expected.items():
        assert len(actual[key]) == len(rows), (database, key, actual[key], rows)
        for got, wanted in zip(actual[key], rows):
            assert got.keys() == wanted.keys(), (key, got, wanted)
            for column, value in wanted.items():
                if isinstance(value, float):
                    assert math.isclose(got[column], value, rel_tol=1e-8), (key, column, got, wanted)
                else:
                    assert got[column] == value, (key, column, got, wanted)
    print(database, len(expected), 'empty/populated cases passed; temporary fixtures rolled back.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--container', required=True, help='Running EMS PostgreSQL container ID/name')
    args = parser.parse_args()
    dlp = 'ems-dlp.json'
    software = 'ems-software-inventory.json'
    security = 'security-posture.json'
    check(args.container, 'fcm_default',
          ['forticlients_users', 'client_software', 'software', 'software_app_control_blocked', 'software_category', 'software_software_category',
           'dlp_agent', 'dlp_agent_config', 'dlp_connector', 'dlp_packages', 'dlp_fct_label',
           'client_vulnerabilities', 'vuln_details'], '''
INSERT INTO software(id,name,vdom_id,blocked,last_used,sessions_last_30_days,first_detected,governance_status)
 VALUES(1,'Fixture A',1,true,now(),9,now(),1),(2,'Fixture B',1,false,NULL,NULL,NULL,-1),
       (3,'Other site',2,true,now(),1000,now(),1);
INSERT INTO software_app_control_blocked(software_id,app_control_profile_id,vdom_id) VALUES(1,1,1),(3,1,2);
INSERT INTO software_category(id,name,vdom_id) VALUES(1,'Fixture category',1);
INSERT INTO software_software_category(software_id,category_id,vdom_id) VALUES(1,1,1),(2,1,1),(3,1,2);
INSERT INTO dlp_agent(id,vdom_id,is_healthy,upgrade_status) VALUES(1,1,true,0),(2,1,false,1),(3,1,NULL,2),(4,2,true,0);
INSERT INTO dlp_agent_config(id,vdom_id,name,enabled) VALUES(1,1,'Fixture A',true),(2,1,'Fixture B',false),(3,2,'Other site',true);
INSERT INTO dlp_connector(id,vdom_id,uuid,host,region,error,api_token_expiry)
 VALUES(1,1,'00000000-0000-0000-0000-000000000001','fixture.invalid','fixture',NULL,now()+interval '1 day'),
       (2,1,'00000000-0000-0000-0000-000000000002','fixture.invalid','fixture','Fixture error',now()-interval '1 day'),
       (3,2,'00000000-0000-0000-0000-000000000003','fixture.invalid','other','Other site error',now()-interval '1 day');
INSERT INTO dlp_packages(assignable_installer_id,package_file_id,vdom_id) VALUES(1,1,1),(2,2,2);
INSERT INTO dlp_fct_label(label_id,client_id,vdom_id,upgrade_version) VALUES(1,1,1,'fixture'),(2,1,1,'fixture'),(3,2,2,'other');
INSERT INTO forticlients_users(id,client_id,vdom_id) VALUES(1,11,1),(2,11,1),(3,12,1),(4,13,2);
INSERT INTO client_software(id,software_id,client_user_id,vdom_id) VALUES(1,1,1,1),(2,1,2,1),(3,2,3,1),(4,3,4,2);
INSERT INTO client_vulnerabilities(client_user_id,vulnerability_id,patch_status,vdom_id)
 VALUES(1,1,0,1),(2,1,0,1),(3,2,0,1),(4,3,0,2);
INSERT INTO vuln_details(vid,title,vdom_id,release_date) VALUES(1,'Fixture known date',1,current_date-10),(2,'Fixture unknown date',1,NULL);
''', [
        (dlp, 'DLP data availability', [{'Collection': 'No DLP agent reports'}], [{'Collection': 'Agent reports present'}]),
        (dlp, 'DLP agents', [{'Agents': 0}], [{'Agents': 3}]),
        (dlp, 'DLP agent healthy %', [{'Healthy %': None}], [{'Healthy %': 100.0 / 3}]),
        (dlp, 'Unhealthy DLP agents', [{'Unhealthy': None}], [{'Unhealthy': 1}]),
        (dlp, 'DLP profiles', [{'Profiles': 0, 'Enabled': 0}], [{'Profiles': 2, 'Enabled': 1}]),
        (dlp, 'DLP connectors', [], [{'Region': 'fixture', 'Connectors': 2, 'With errors': 1, 'Expired credentials': 1}]),
        (dlp, 'DLP package assignments', [{'Package assignments': 0}], [{'Package assignments': 1}]),
        (dlp, 'DLP-labelled endpoints', [{'Endpoints': 0}], [{'Endpoints': 1}]),
        (software, 'Software data availability', [{'Collection': 'No software catalogue data'}], [{'Collection': 'Catalogue data present'}]),
        (software, 'Blocked catalogue packages', [{'Blocked': 0}], [{'Blocked': 1}]),
        (software, 'Packages with usage reports', [{'Packages': 0}], [{'Packages': 1}]),
        (software, 'Reported sessions (30d)', [{'Sessions': None}], [{'Sessions': 9}]),
        (software, 'Application-control blocks', [{'Policy-package mappings': 0, 'Distinct packages': 0}], [{'Policy-package mappings': 1, 'Distinct packages': 1}]),
        (software, 'Software categories', [], [{'Category': 'Fixture category', 'Packages': 2}]),
        (software, 'Top Installed Packages', [], [
            {'Software':'Fixture A','Vendor':'Unknown','Version':'Unknown','Endpoints':1},
            {'Software':'Fixture B','Vendor':'Unknown','Version':'Unknown','Endpoints':1}]),
        (software, 'Vendor Distribution', [], [{'Vendor':'Unknown','Endpoints':2}]),
        (security, 'Unpatched Vulnerabilities by Severity',
            [{'Critical':0,'High':0,'Medium':0,'Low':0,'Unknown':0}],
            [{'Critical':0,'High':0,'Medium':0,'Low':0,'Unknown':2}]),
        (security, 'Top Unpatched Vulnerabilities', [], [
            {'CVEs':'VID 1','Title':'Fixture known date','Severity':'Unknown','CVSS':None,'Affected Endpoints':1},
            {'CVEs':'VID 2','Title':'Fixture unknown date','Severity':'Unknown','CVSS':None,'Affected Endpoints':1}]),
        (security, 'Unpatched vulnerabilities by publication date', [], [
            {'Vulnerability':'VID 1','Published':(datetime.now(timezone.utc).date()-timedelta(days=10)).isoformat(),'Days since publication':10,'Affected endpoints':1},
            {'Vulnerability':'VID 2','Published':None,'Days since publication':None,'Affected endpoints':1}]),
        (security, 'Endpoints with Unpatched Vulns', [{'Affected Endpoints': 0}], [{'Affected Endpoints': 2}]),
        (security, 'Unpatched detections with known publication date %', [{'Known date %': None}], [{'Known date %': 200.0 / 3}]),
        (security, 'Unpatched detections with unknown publication date', [{'Unknown dates': 0}], [{'Unknown dates': 1}]),
    ])
    admin = 'ems-admin-licensing.json'
    check(args.container, 'fcm', ['hotfix_info', 'system_settings_v2'], '''
INSERT INTO hotfix_info(id,hotfix_available,hotfix_scheduled_date,is_auto)
 VALUES(1,'FIXTURE-1',now(),true),(2,'[]',NULL,false),(3,NULL,NULL,false);
''', [
        (admin, 'Hotfix schedules', [{'Scheduled': 0}], [{'Scheduled': 1}]),
        (admin, 'Hotfix advertised', [{'Advertised': 0}], [{'Advertised': 1}]),
        (admin, 'Hotfix catalogue rows', [{'Rows': 0}], [{'Rows': 3}]),
    ])


if __name__ == '__main__':
    main()
