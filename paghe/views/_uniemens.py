"""Export UNIEMENS CSV per commercialisti/CAF."""

from paghe.views._common_imports import *
from paghe.views._helpers import _decodifica_cf
import csv


MESI_UNIEMENS = ['', '01', '02', '03', '04', '05', '06',
                 '07', '08', '09', '10', '11', '12']


@login_required
@never_cache
def export_uniemens_csv(request):
    oggi = date.today()
    anno = int(request.GET.get('anno', oggi.year))
    mese = int(request.GET.get('mese', oggi.month))
    request.GET.get('tipo', 'MENSILE')

    qs = BustaPaga.objects.filter(
        mese=mese, anno=anno,
    ).select_related(
        'contratto__datore',
        'contratto__lavoratore',
    ).order_by('contratto__datore__nome_cognome', 'contratto__lavoratore__nome_cognome')

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="UNIEMENS_{MESI_UNIEMENS[mese]}_{anno}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'CF Datore', 'Cognome Datore', 'Nome Datore',
        'CF Lavoratore', 'Cognome Lavoratore', 'Nome Lavoratore',
        'Sesso', 'Data Nascita', 'Comune Nascita', 'Provincia Nascita',
        'Mese', 'Anno',
        'Tipo Calcolo', 'Ore INPS', 'Paga Oraria Lorda',
        'Imponibile Lordo', 'Contributi INPS', 'Contributi Cassa',
        'Netto', 'Codice Rapporto INPS',
    ])

    for bp in qs:
        c = bp.contratto
        anag = _decodifica_cf(c.lavoratore.codice_fiscale) if c.lavoratore.codice_fiscale else {}
        cognome_lav = (c.lavoratore.cognome or '').strip()
        nome_lav = (c.lavoratore.nome or '').strip()
        if not cognome_lav and not nome_lav:
            nc = (c.lavoratore.nome_cognome or '').strip()
            parti = nc.split(' ', 1)
            cognome_lav = parti[0] if len(parti) > 0 else nc
            nome_lav = parti[1] if len(parti) > 1 else ''

        cognome_dat = (c.datore.cognome or '').strip()
        nome_dat = (c.datore.nome or '').strip()
        if not cognome_dat and not nome_dat:
            nc = (c.datore.nome_cognome or '').strip()
            parti = nc.split(' ', 1)
            cognome_dat = parti[0] if len(parti) > 0 else nc
            nome_dat = parti[1] if len(parti) > 1 else ''

        writer.writerow([
            c.datore.codice_fiscale or '',
            cognome_dat, nome_dat,
            c.lavoratore.codice_fiscale or '',
            cognome_lav, nome_lav,
            anag.get('sesso', '')[:1] if anag else '',
            anag.get('data_nascita', '') if anag else '',
            anag.get('comune_nascita', '') if anag else '',
            anag.get('provincia_nascita', '') if anag else '',
            MESI_UNIEMENS[mese], str(anno),
            bp.tipo_calcolo,
            bp.ore_inps,
            f'{bp.paga_oraria_lorda:.4f}',
            f'{bp.totale_lordo:.2f}',
            f'{bp.contributi_inps_totale:.2f}',
            f'{bp.contributi_cassa_totale:.2f}',
            f'{bp.netto:.2f}',
            c.codice_rapporto_inps or '',
        ])

    return response
