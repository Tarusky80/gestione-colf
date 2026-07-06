"""Modulo _contratto_pdf - generazione contratti via Playwright"""

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.views._helpers import _get_cartella_documenti, _genera_pdf_da_testo_playwright
from paghe.views._testi import _risolvi_variabili_testo




# --- anteprima_contratto ---
@login_required
@permesso_richiesto('contratti.vedi')
@never_cache
def anteprima_contratto(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    pk_testo = request.GET.get('testo')
    if pk_testo:
        testo = get_object_or_404(ModelloDocumentale, pk=pk_testo, tipo='CONTRATTO')
    else:
        testo = ModelloDocumentale.objects.filter(tipo='CONTRATTO').first()
    if not testo:
        return HttpResponse("Nessun modello contratto trovato. Creane uno in Gestione Documentale con tipo 'CONTRATTO'.", status=404)
    corpo_risolto = _risolvi_variabili_testo(testo.corpo_testo, contratto)
    oggetto_risolto = _risolvi_variabili_testo(testo.titolo, contratto)
    opzioni = get_opzioni()
    primo_progetto = contratto.progetto.first()
    nome_beneficiario = primo_progetto.beneficiario.nome_cognome if primo_progetto and primo_progetto.beneficiario else '_______________'
    template = 'paghe/contratto_anteprima_embed.html' if request.GET.get('embed') else 'paghe/contratto_anteprima.html'
    return render(request, template, {
        'contratto': contratto,
        'testo': testo,
        'oggetto_risolto': oggetto_risolto,
        'corpo_risolto': corpo_risolto,
        'opzioni': opzioni,
        'nome_beneficiario': nome_beneficiario,
    })


# --- download_contratto_pdf ---
@login_required
@permesso_richiesto('contratti.vedi')
@never_cache
def download_contratto_pdf(request, pk):
    import base64
    from datetime import date
    from PIL import Image as PilImage

    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    pk_testo = request.GET.get('testo')
    if pk_testo:
        testo = get_object_or_404(ModelloDocumentale, pk=pk_testo, tipo='CONTRATTO')
    else:
        testo = ModelloDocumentale.objects.filter(tipo='CONTRATTO').first()
    if not testo:
        return HttpResponse("Nessun modello contratto trovato.", status=404)

    corpo_risolto = _risolvi_variabili_testo(testo.corpo_testo, contratto)
    _risolvi_variabili_testo(testo.titolo, contratto)
    opzioni = get_opzioni()
    oggi = date.today()

    primo_progetto = contratto.progetto.first()
    nome_beneficiario = primo_progetto.beneficiario.nome_cognome if primo_progetto and primo_progetto.beneficiario else '_______________'
    titolo_contratto = f"CONTRATTO DI LAVORO DOMESTICO TRA {contratto.datore.nome_cognome} E {contratto.lavoratore.nome_cognome} PER ASSISTENZA {nome_beneficiario}"

    corpo_completo = f"""
{corpo_risolto}

<hr style="border:none;border-top:1px solid #ccc;margin:18px 0;">

<div style="margin-top:8px;font-size:11pt;color:#333;">
    Luogo e data, {contratto.datore.comune or '_______________'}, {oggi.strftime('%d/%m/%Y')}
</div>
<div style="margin-top:20px;display:flex;justify-content:space-between;font-size:10pt;color:#666;line-height:1.6;">
    <div style="text-align:center;width:45%;">
        <div style="font-size:11pt;color:#333;margin-bottom:4px;font-weight:bold;">FIRMA DEL DATORE DI LAVORO</div>
        <span style="border-bottom:1px solid #666;display:inline-block;width:100%;">&nbsp;</span>
        <div style="font-size:10pt;color:#999;margin-top:4px;">({contratto.datore.nome_cognome})</div>
    </div>
    <div style="text-align:center;width:45%;">
        <div style="font-size:11pt;color:#333;margin-bottom:4px;font-weight:bold;">FIRMA DEL LAVORATORE</div>
        <span style="border-bottom:1px solid #666;display:inline-block;width:100%;">&nbsp;</span>
        <div style="font-size:10pt;color:#999;margin-top:4px;">({contratto.lavoratore.nome_cognome})</div>
    </div>
</div>

<div style="margin-top:24px;">
    <div style="font-size:9pt;font-weight:bold;color:#333;margin-bottom:6px;">DATI STUDIO</div>"""

    # --- Logo DATI STUDIO in base64 per Playwright ---
    if opzioni:
        if opzioni.logo_buste_paga and opzioni.logo_buste_paga.path and os.path.exists(opzioni.logo_buste_paga.path):
            try:
                with PilImage.open(opzioni.logo_buste_paga.path) as pil_img:
                    _ow, _oh = pil_img.size
                with open(opzioni.logo_buste_paga.path, 'rb') as f:
                    img_b64 = base64.b64encode(f.read()).decode('utf-8')
                ext = opzioni.logo_buste_paga.path.rsplit('.', 1)[-1].lower()
                if ext == 'jpg': ext = 'jpeg'
                corpo_completo += f"""
    <div style="margin-bottom:4px;">
        <img src="data:image/{ext};base64,{img_b64}" style="max-height:30px;max-width:120px;" alt="Logo studio">
    </div>"""
            except Exception:
                logger.exception("Errore in download_contratto_pdf")
                pass
        studio_parts = list(filter(None, [
            opzioni.dati_studio,
            f"Tel: {opzioni.telefono_studio}" if opzioni.telefono_studio else None,
            f"Mail: {opzioni.email_studio}" if opzioni.email_studio else None,
        ]))
        if studio_parts:
            corpo_completo += f"""
    <div style="font-size:8pt;color:#999;">
        {" | ".join(studio_parts)}
    </div>"""

    corpo_completo += f"""
</div>

<div style="margin-top:20px;padding-top:12px;border-top:1.5px solid #ccc;font-size:7pt;color:#999;text-align:center;">
    Tutti i diritti riservati: &egrave; vietata la riproduzione, anche parziale, dei contenuti. | Stampata il {oggi.strftime('%d/%m/%Y')}
</div>"""

    # --- Genera PDF via Playwright ---
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"contratto_{safe_name}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)

    _genera_pdf_da_testo_playwright(
        titolo=titolo_contratto,
        corpo=corpo_completo,
        output_path=full_path,
        font_family=testo.font_family or 'Arial',
        font_size=testo.font_size or 11
    )

    with open(full_path, 'rb') as f:
        pdf = f.read()

    nome_file = f"contratto_{contratto.lavoratore.nome_cognome.replace(' ', '_')}.pdf"

    DocumentoArchiviato.objects.create(
        tipo='CONTRATTO',
        titolo=f"Contratto {contratto.lavoratore.nome_cognome}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        modello_documentale=testo,
        creato_da=request.user if request.user.is_authenticated else None,
    )

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response


# --- ajax_genera_contratto_pdf (per finestra flottante) ---
@login_required
@permesso_richiesto('contratti.crea')
@never_cache
def ajax_genera_contratto_pdf(request, pk):
    """Genera PDF contratto, salva in archivio, torna PK per finestra flottante."""
    import base64
    from datetime import date
    from PIL import Image as PilImage

    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    pk_testo = request.POST.get('testo') or request.GET.get('testo')
    if pk_testo:
        testo = get_object_or_404(ModelloDocumentale, pk=pk_testo, tipo='CONTRATTO')
    else:
        testo = ModelloDocumentale.objects.filter(tipo='CONTRATTO').first()
    if not testo:
        return JsonResponse({'ok': False, 'errore': 'Nessun modello contratto trovato.'}, status=404)

    corpo_risolto = _risolvi_variabili_testo(testo.corpo_testo, contratto)
    opzioni = get_opzioni()
    oggi = date.today()

    primo_progetto = contratto.progetto.first()
    nome_beneficiario = primo_progetto.beneficiario.nome_cognome if primo_progetto and primo_progetto.beneficiario else '_______________'
    titolo_contratto = f"CONTRATTO DI LAVORO DOMESTICO TRA {contratto.datore.nome_cognome} E {contratto.lavoratore.nome_cognome} PER ASSISTENZA {nome_beneficiario}"

    corpo_completo = f"""
{corpo_risolto}

<hr style="border:none;border-top:1px solid #ccc;margin:18px 0;">

<div style="margin-top:8px;font-size:11pt;color:#333;">
    Luogo e data, {contratto.datore.comune or '_______________'}, {oggi.strftime('%d/%m/%Y')}
</div>
<div style="margin-top:20px;display:flex;justify-content:space-between;font-size:10pt;color:#666;line-height:1.6;">
    <div style="text-align:center;width:45%;">
        <div style="font-size:11pt;color:#333;margin-bottom:4px;font-weight:bold;">FIRMA DEL DATORE DI LAVORO</div>
        <span style="border-bottom:1px solid #666;display:inline-block;width:100%;">&nbsp;</span>
        <div style="font-size:10pt;color:#999;margin-top:4px;">({contratto.datore.nome_cognome})</div>
    </div>
    <div style="text-align:center;width:45%;">
        <div style="font-size:11pt;color:#333;margin-bottom:4px;font-weight:bold;">FIRMA DEL LAVORATORE</div>
        <span style="border-bottom:1px solid #666;display:inline-block;width:100%;">&nbsp;</span>
        <div style="font-size:10pt;color:#999;margin-top:4px;">({contratto.lavoratore.nome_cognome})</div>
    </div>
</div>

<div style="margin-top:24px;">
    <div style="font-size:9pt;font-weight:bold;color:#333;margin-bottom:6px;">DATI STUDIO</div>"""

    if opzioni:
        if opzioni.logo_buste_paga and opzioni.logo_buste_paga.path and os.path.exists(opzioni.logo_buste_paga.path):
            try:
                with PilImage.open(opzioni.logo_buste_paga.path) as pil_img:
                    _ow, _oh = pil_img.size
                with open(opzioni.logo_buste_paga.path, 'rb') as f:
                    img_b64 = base64.b64encode(f.read()).decode('utf-8')
                ext = opzioni.logo_buste_paga.path.rsplit('.', 1)[-1].lower()
                if ext == 'jpg': ext = 'jpeg'
                corpo_completo += f"""
    <div style="margin-bottom:4px;">
        <img src="data:image/{ext};base64,{img_b64}" style="max-height:30px;max-width:120px;" alt="Logo studio">
    </div>"""
            except Exception:
                logger.warning("Impossibile caricare logo contratto (firme): %s", getattr(opzioni.logo_buste_paga, 'path', ''))
        studio_parts = list(filter(None, [
            opzioni.dati_studio,
            f"Tel: {opzioni.telefono_studio}" if opzioni.telefono_studio else None,
            f"Mail: {opzioni.email_studio}" if opzioni.email_studio else None,
        ]))
        if studio_parts:
            corpo_completo += f"""
    <div style="font-size:8pt;color:#999;">
        {" | ".join(studio_parts)}
    </div>"""

    corpo_completo += f"""
</div>

<div style="margin-top:20px;padding-top:12px;border-top:1.5px solid #ccc;font-size:7pt;color:#999;text-align:center;">
    Tutti i diritti riservati: &egrave; vietata la riproduzione, anche parziale, dei contenuti. | Stampata il {oggi.strftime('%d/%m/%Y')}
</div>"""

    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"contratto_{safe_name}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)

    _genera_pdf_da_testo_playwright(
        titolo=titolo_contratto,
        corpo=corpo_completo,
        output_path=full_path,
        font_family=testo.font_family or 'Arial',
        font_size=testo.font_size or 11
    )

    with open(full_path, 'rb') as f:
        pdf = f.read()

    doc = DocumentoArchiviato.objects.create(
        tipo='CONTRATTO',
        titolo=f"Contratto {contratto.lavoratore.nome_cognome}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        modello_documentale=testo,
        creato_da=request.user if request.user.is_authenticated else None,
    )

    return JsonResponse({
        'ok': True,
        'pk': doc.pk,
        'url': f'/ajax/vedi-documento/{doc.pk}/',
        'file_name': nome_file_disk,
        'file_size': len(pdf),
    })
