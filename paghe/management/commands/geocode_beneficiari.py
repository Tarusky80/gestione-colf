import json
import time
import requests
from pathlib import Path
from django.core.management.base import BaseCommand
from paghe.models import Beneficiario

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "GestioneColf/2.0 (gestionecolf@local)"

class Command(BaseCommand):
    help = "Geocodifica tutti i beneficiari via Nominatim e salva cache JSON"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Rigeocodifica anche se già presenti')

    def handle(self, *args, **options):
        force = options['force']
        cache_path = Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'coordinate_beneficiari.json'

        if cache_path.exists() and not force:
            try:
                cache = json.loads(cache_path.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, KeyError):
                cache = {}
        else:
            cache = {}

        qs = Beneficiario.objects.exclude(indirizzo='').exclude(comune='')
        totale = qs.count()
        if totale == 0:
            self.stdout.write(self.style.WARNING("Nessun beneficiario con indirizzo da geocodificare"))
            return

        nuovo = 0
        saltati = 0
        for i, b in enumerate(qs, 1):
            if b.codice_fiscale in cache and not force:
                saltati += 1
                continue
            ind_full = f"{b.indirizzo}, {b.comune}"
            if b.provincia:
                ind_full += f", {b.provincia}"
            if b.cap:
                ind_full += f" {b.cap}"

            params = {'q': ind_full, 'format': 'json', 'limit': 1}
            headers = {'User-Agent': USER_AGENT}
            try:
                r = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=15)
                data = r.json()
                if data:
                    lat = float(data[0]['lat'])
                    lng = float(data[0]['lon'])
                else:
                    lat = lng = None
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [{i}/{totale}] ERRORE {b.nome_cognome}: {e}"))
                lat = lng = None

            cache[b.codice_fiscale] = {
                'lat': lat,
                'lng': lng,
                'nome': b.nome_cognome,
                'indirizzo': b.indirizzo,
                'comune': b.comune,
                'provincia': b.provincia,
            }
            if lat is not None:
                nuovo += 1
                self.stdout.write(f"  [{i}/{totale}] OK {b.nome_cognome} -> {lat:.4f}, {lng:.4f}")
            else:
                # Fallback: cerca solo comune
                time.sleep(1.1)
                try:
                    r2 = requests.get(NOMINATIM_URL, params={'q': f"{b.comune}, Italia", 'format': 'jsonv2', 'limit': 1}, headers=headers, timeout=15)
                    d2 = r2.json()
                    if d2 and d2[0].get('lat') and d2[0].get('lon'):
                        lat, lng = float(d2[0]['lat']), float(d2[0]['lon'])
                        cache[b.codice_fiscale]['lat'] = lat
                        cache[b.codice_fiscale]['lng'] = lng
                        cache[b.codice_fiscale]['indirizzo'] = f"{b.comune} (approssimato)"
                        nuovo += 1
                        self.stdout.write(f"  FALLBACK {b.nome_cognome} -> {lat:.4f}, {lng:.4f} (solo comune)")
                    else:
                        self.stdout.write(self.style.WARNING(f"  [{i}/{totale}] NON TROVATO {b.nome_cognome} ({ind_full})"))
                except Exception:
                    self.stdout.write(self.style.WARNING(f"  [{i}/{totale}] NON TROVATO {b.nome_cognome} ({ind_full})"))
            time.sleep(1.1)

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding='utf-8')
        self.stdout.write(f"\n[OK] Fatto: {nuovo} nuovi, {saltati} già in cache. File: {cache_path}")
