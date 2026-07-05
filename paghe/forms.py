from django import forms
from .models import DatoreLavoro, Lavoratore, Beneficiario, ProgettoRegionale, ContrattoLavoro, OpzioniSoftware, ParametriCCNL, TabellaCasse, TabellaContributiINPS, TabellaMalattia, TabellaScattiAnzianita, TipoProgettoRegionale, Livello, DocumentoArchiviato, ModelloLista, ModelloComposizione

class BaseLinearForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                continue  # rendered manually in template
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.Textarea, forms.NumberInput, forms.DateInput, forms.Select, forms.URLInput, forms.ClearableFileInput, forms.FileInput)):
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['style'] = (
                    'background-color: #09090B; '
                    'border: 1px solid #27282D; '
                    'color: #ffffff; '
                    'font-size: 14px; '
                    'padding: 10px 12px; '
                    'border-radius: 8px;'
                )
            
            # Styling specifico per checkbox
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'

class DatoreForm(BaseLinearForm):
    class Meta:
        model = DatoreLavoro
        fields = '__all__'
        exclude = ['nome_cognome']
        widgets = {
            'visibile_a': forms.CheckboxSelectMultiple,
        }

class LavoratoreForm(BaseLinearForm):
    class Meta:
        model = Lavoratore
        fields = '__all__'
        exclude = ['nome_cognome']
        widgets = {
            'visibile_a': forms.CheckboxSelectMultiple,
        }

class BeneficiarioForm(BaseLinearForm):
    class Meta:
        model = Beneficiario
        fields = '__all__'
        exclude = ['nome_cognome']

class ContrattoForm(BaseLinearForm):
    class Meta:
        model = ContrattoLavoro
        fields = '__all__'
        exclude = ['ore_calcolate', 'paga_tfr', 'giorni_malattia_usati_anno']
        widgets = {
            'progetto': forms.CheckboxSelectMultiple,
            'visibile_a': forms.CheckboxSelectMultiple,
            'data_assunzione': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_inizio_tfr': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_fine': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'modalita_tfr': forms.HiddenInput,
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance

class OpzioniSoftwareForm(BaseLinearForm):
    class Meta:
        model = OpzioniSoftware
        fields = '__all__'
        widgets = {
            'logo': forms.FileInput,
            'logo_buste_paga': forms.FileInput,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter testi preimpostati to only TESTO_PROGRAMMA type for the FK fields
        from .models import ModelloDocumentale
        tp_qs = ModelloDocumentale.objects.filter(tipo='TESTO_PROGRAMMA')
        if 'testo_alert_contributi' in self.fields:
            self.fields['testo_alert_contributi'].queryset = tp_qs
            self.fields['testo_alert_contributi'].empty_label = '-- Nessuno --'
        if 'testo_note_avvertenze' in self.fields:
            self.fields['testo_note_avvertenze'].queryset = tp_qs
            self.fields['testo_note_avvertenze'].empty_label = '-- Nessuno --'
        if 'testo_note_footer_mail' in self.fields:
            self.fields['testo_note_footer_mail'].queryset = tp_qs
            self.fields['testo_note_footer_mail'].empty_label = '-- Nessuno --'
        if 'testo_firma_email' in self.fields:
            self.fields['testo_firma_email'].queryset = tp_qs
            self.fields['testo_firma_email'].empty_label = '-- Nessuno --'

class ProgettoRegionaleForm(BaseLinearForm):
    class Meta:
        model = ProgettoRegionale
        fields = '__all__'
        widgets = {
            'data_inizio': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'data_fine': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

class ParametriCCNLForm(BaseLinearForm):
    class Meta:
        model = ParametriCCNL
        fields = '__all__'

class TabellaCasseForm(BaseLinearForm):
    class Meta:
        model = TabellaCasse
        fields = '__all__'

class TabellaContributiINPSForm(BaseLinearForm):
    class Meta:
        model = TabellaContributiINPS
        fields = '__all__'

class TabellaMalattiaForm(BaseLinearForm):
    class Meta:
        model = TabellaMalattia
        fields = '__all__'

class TabellaScattiAnzianitaForm(BaseLinearForm):
    class Meta:
        model = TabellaScattiAnzianita
        fields = '__all__'

class ModelloListaForm(BaseLinearForm):
    class Meta:
        model = ModelloLista
        fields = ['nome', 'tipo_sorgente', 'note', 'is_default']


class TipoProgettoRegionaleForm(BaseLinearForm):
    class Meta:
        model = TipoProgettoRegionale
        fields = '__all__'
        widgets = {
            'colore': forms.TextInput(attrs={'type': 'color', 'style': 'height:42px;padding:3px;cursor:pointer;border-radius:6px;', 'oninput': 'aggiornaHexColore(this)'}),
        }

class LivelloForm(BaseLinearForm):
    class Meta:
        model = Livello
        fields = '__all__'
        widgets = {
            'colore': forms.TextInput(attrs={'type': 'color', 'style': 'height:42px;padding:3px;cursor:pointer;border-radius:6px;', 'oninput': 'aggiornaHexColore(this)'}),
        }

class ModelloComposizioneForm(BaseLinearForm):
    class Meta:
        model = ModelloComposizione
        fields = ['nome', 'note', 'is_default']

class DocumentoArchiviatoForm(BaseLinearForm):
    class Meta:
        model = DocumentoArchiviato
        fields = ['tipo', 'titolo', 'contratto', 'datore', 'lavoratore', 'modello_testo', 'note']