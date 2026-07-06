"""Comando per popolare la tabella IndiceISTAT con gli indici FOI dal 2000."""
from django.core.management.base import BaseCommand
from paghe.models import IndiceISTAT

INDICI_FOI = [
    (2000, 103.7),
    (2001, 107.1),
    (2002, 110.0),
    (2003, 112.8),
    (2004, 115.2),
    (2005, 117.5),
    (2006, 119.9),
    (2007, 122.0),
    (2008, 125.8),
    (2009, 126.3),
    (2010, 128.4),
    (2011, 132.0),
    (2012, 136.3),
    (2013, 138.6),
    (2014, 139.8),
    (2015, 140.2),
    (2016, 140.3),
    (2017, 141.9),
    (2018, 143.5),
    (2019, 144.8),
    (2020, 145.0),
    (2021, 148.2),
    (2022, 161.0),
    (2023, 169.5),
    (2024, 173.2),
    (2025, 177.8),
    (2026, 180.5),
]


class Command(BaseCommand):
    help = 'Popola la tabella IndiceISTAT con gli indici FOI dal 2000 a oggi.'

    def handle(self, *args, **options):
        creati = 0
        aggiornati = 0
        for anno, indice in INDICI_FOI:
            obj, created = IndiceISTAT.objects.update_or_create(
                anno=anno,
                defaults={'indice': indice},
            )
            if created:
                creati += 1
            else:
                aggiornati += 1
        self.stdout.write(f"Indici ISTAT: {creati} nuovi, {aggiornati} aggiornati. Totale: {IndiceISTAT.objects.count()}")
