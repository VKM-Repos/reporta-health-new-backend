"""
Management command: import_hfr_data
Place at: apps/facilities/management/commands/import_hfr_data.py
(create the management/commands/ directories with __init__.py files if they don't exist)

Usage:
    python manage.py import_hfr_data --dir ~/hfr_export --dry-run   # preview counts only
    python manage.py import_hfr_data --dir ~/hfr_export             # actually import
"""
import csv
import re
from pathlib import Path

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.facilities.models import Facility, Service

COORD_RE = re.compile(r'^-?\d+\.?\d*$')

# facility_type string used in facility_services.tsv -> Facility.FACILITY_TYPES choice
SOURCE_TYPE_TO_FACILITY_TYPE = {
    'hospital': 'hospital',
    'pharmacy': 'pharmacy',
    'laboratory': 'laboratory',
    'imaging': 'diagnostic',
    'legal': 'legal_aid',
    'other': 'other',  # refined per-row below using `type` column where available
}

# other_service_providers.type / legal_facilities.type -> better facility_type guess
OTHER_TYPE_KEYWORDS = {
    'ngo': 'ngo',
    'police': 'police',
    'security': 'other',
    'welfare': 'social_welfare',
    'shelter': 'shelter',
    'refuge': 'shelter',
}


def parse_float(val):
    if val and COORD_RE.match(val.strip()):
        return float(val.strip())
    return None


def guess_other_facility_type(raw_type):
    if not raw_type:
        return 'other'
    low = raw_type.lower()
    for kw, ftype in OTHER_TYPE_KEYWORDS.items():
        if kw in low:
            return ftype
    return 'ngo'  # default for other_service_providers if nothing matches


def read_tsv(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            yield row


class Command(BaseCommand):
    help = "Import harmonized HFR data (hospitals/pharmacy/lab/imaging/legal/other + NHIA + services) into Facility/Service"

    def add_arguments(self, parser):
        parser.add_argument('--dir', required=True, help='Directory containing the exported .tsv files')
        parser.add_argument('--dry-run', action='store_true', help='Preview counts without writing to DB')

    def handle(self, *args, **opts):
        base = Path(opts['dir']).expanduser()
        dry_run = opts['dry_run']

        # ---------- 1. Services catalog ----------
        services_path = base / 'services.tsv'
        service_map = {}  # hfr service_id (int) -> Service instance
        service_rows = list(read_tsv(services_path))
        self.stdout.write(f"Services catalog: {len(service_rows)} rows")

        if not dry_run:
            with transaction.atomic():
                for row in service_rows:
                    svc, _ = Service.objects.update_or_create(
                        hfr_service_id=int(row['service_id']),
                        defaults={
                            'name': row['service_name'][:96],
                            'category': (row.get('category') or 'support').lower()[:32],
                        },
                    )
                    service_map[int(row['service_id'])] = svc
        else:
            for row in service_rows:
                service_map[int(row['service_id'])] = None  # placeholder for dry run

        # ---------- 2. NHIA accreditation lookup: facility_id -> (accepted, code) ----------
        nhia_path = base / 'nhia.tsv'
        nhia_map = {}
        for row in read_tsv(nhia_path):
            fid = row['facility_id']
            # nhia.tsv facility_id here is the NHIA table's own PK (NHIA000xxx),
            # actual join key is via nhia_status already present on hospitals.tsv row directly,
            # AND via facility_id/facility_type pair matching source tables — use that pair.
            key = (row.get('facility_type', 'hospital'), row.get('facility_id'))
            nhia_map[key] = row
        self.stdout.write(f"NHIA lookup rows: {len(nhia_map)}")

        # ---------- 3. facility_services -> facility_id+type -> [service_ids] ----------
        fs_path = base / 'facility_services.tsv'
        fs_map = {}
        for row in read_tsv(fs_path):
            key = (row['facility_type'], row['facility_id'])
            fs_map.setdefault(key, []).append(int(row['service_id']))
        self.stdout.write(f"facility_services link rows loaded, {len(fs_map)} unique facilities with services")

        # ---------- 4. Source table configs ----------
        sources = [
            ('hospital', base / 'hospitals.tsv'),
            ('pharmacy', base / 'pharmacy.tsv'),
            ('laboratory', base / 'laboratory.tsv'),
            ('imaging', base / 'imaging.tsv'),
            ('legal', base / 'legal.tsv'),
            ('other', base / 'other.tsv'),
        ]

        total_created = 0
        total_skipped = 0
        BATCH = 2000
        ThroughModel = Facility.services_offered.through

        for source_type, path in sources:
            if not path.exists():
                self.stdout.write(self.style.WARNING(f"Missing file: {path}, skipping"))
                continue

            rows = list(read_tsv(path))
            self.stdout.write(f"\n--- {source_type}: {len(rows)} rows ---")

            to_create = []       # Facility() unsaved instances
            svc_lookup = []      # parallel list: list[int] hfr service_ids per facility, aligned with to_create

            for row in rows:
                name = (row.get('name') or '').strip()
                if not name or 'web server is returning' in name.lower() or name.lower() == 'database error':
                    total_skipped += 1
                    continue

                facility_id = row.get('facility_id', '')

                if source_type == 'other':
                    ftype = guess_other_facility_type(row.get('type', ''))
                elif source_type == 'legal':
                    ftype = 'legal_aid'
                else:
                    ftype = SOURCE_TYPE_TO_FACILITY_TYPE[source_type]

                lat = parse_float(row.get('latitude', '')) if source_type == 'hospital' else None
                lon = parse_float(row.get('longitude', '')) if source_type == 'hospital' else None
                location = Point(lon, lat, srid=4326) if (lat is not None and lon is not None) else None

                nhia_row = nhia_map.get((source_type, facility_id))
                nhia_status_val = row.get('nhia_status', '') or (nhia_row['nhia_status'] if nhia_row else '')
                nhia_accepted = nhia_status_val.strip().lower() == 'accredited'
                nhia_code = nhia_row['nhia_code'] if nhia_row else ''

                fac = Facility(
                    name=name[:255],
                    facility_type=ftype,
                    sig_unique_id='',
                    address=(row.get('address') or '')[:5000],
                    location=location,
                    state=(row.get('state') or '')[:100],
                    lga=(row.get('lga') or '')[:100],
                    ward=(row.get('ward') or '')[:150],
                    phone_number=(row.get('phone') or '')[:20],
                    email=(row.get('email') or '')[:254] if '@' in (row.get('email') or '') else '',
                    website=(row.get('website') or '')[:200] if source_type == 'hospital' else '',
                    ownership=map_ownership(row.get('ownership', '')) if source_type == 'hospital' else 'private',
                    services=(row.get('services') or '')[:5000] if source_type in ('legal', 'other') else '',
                    nhia_accepted=nhia_accepted,
                    nhia_code=(nhia_code or '')[:255],
                    license_status=(row.get('license_status') or '')[:100] if source_type == 'hospital' else (row.get('reg_status') or '')[:100],
                    availability=(row.get('availability') or '')[:100],
                    cost=(row.get('cost') or '')[:100],
                )
                to_create.append(fac)
                svc_lookup.append(fs_map.get((source_type, facility_id), []))

            created_here = len(to_create)

            if not dry_run and to_create:
                total_batches = (len(to_create) + BATCH - 1) // BATCH
                created_objs_all = []
                for i in range(0, len(to_create), BATCH):
                    batch_slice = to_create[i:i + BATCH]
                    with transaction.atomic():
                        created_objs = Facility.objects.bulk_create(batch_slice, batch_size=BATCH)
                    created_objs_all.extend(created_objs)
                    self.stdout.write(
                        f"  [{source_type}] facilities: {min(i + BATCH, len(to_create))}/{len(to_create)} "
                        f"(batch {i // BATCH + 1}/{total_batches})"
                    )

                # build through-table rows for M2M in bulk, also batched with progress
                through_rows = []
                for fac, svc_ids in zip(created_objs_all, svc_lookup):
                    for sid in svc_ids:
                        svc = service_map.get(sid)
                        if svc:
                            through_rows.append(ThroughModel(facility_id=fac.pk, service_id=svc.pk))

                if through_rows:
                    total_link_batches = (len(through_rows) + BATCH - 1) // BATCH
                    for i in range(0, len(through_rows), BATCH):
                        with transaction.atomic():
                            ThroughModel.objects.bulk_create(
                                through_rows[i:i + BATCH], batch_size=BATCH, ignore_conflicts=True
                            )
                        self.stdout.write(
                            f"  [{source_type}] service links: {min(i + BATCH, len(through_rows))}/{len(through_rows)} "
                            f"(batch {i // BATCH + 1}/{total_link_batches})"
                        )

            total_created += created_here
            self.stdout.write(self.style.SUCCESS(f"{source_type}: {created_here} facilities {'would be ' if dry_run else ''}created"))

        self.stdout.write(self.style.SUCCESS(f"\nTOTAL: {total_created} facilities {'would be ' if dry_run else ''}created, {total_skipped} skipped (junk names)"))


def map_ownership(raw):
    if not raw:
        return 'private'
    low = raw.lower()
    if 'federal' in low:
        return 'federal_government'
    if 'state' in low:
        return 'state_government'
    if 'lga' in low or 'local' in low:
        return 'lga'
    if 'mission' in low or 'faith' in low:
        return 'mission'
    if 'ngo' in low:
        return 'ngo'
    if 'private' in low:
        return 'private'
    return 'other'
