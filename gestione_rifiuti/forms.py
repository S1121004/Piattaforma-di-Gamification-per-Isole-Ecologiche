import re # Importa la libreria 're' (Regular Expressions), usata per controllare se una stringa rispetta un formato preciso (es. il formato del codice fiscale)
from django import forms # Importa il sistema dei moduli (forms) di Django, che semplifica la creazione di form HTML e ne valida i dati
from django.contrib.auth.models import User # Importa il modello utente di base di Django
from django.db.models import Max # Importa la funzione 'Max' per trovare il numero più alto in una colonna del database (ci servirà per calcolare l'ID)
from .models import Conferimento, Cittadino # Importa dal tuo file models.py i modelli Conferimento e Cittadino
from .models import TipologiaRifiuto # Importa sempre dal tuo file models.py il modello TipologiaRifiuto

class ConferimentoForm(forms.ModelForm): # Crea un modulo basato direttamente su un modello del database (ModelForm)
    class Meta: # La classe Meta serve a dire a Django come deve comportarsi questo modulo
        model = Conferimento # Indica che questo form serve a inserire/modificare dati nella tabella 'Conferimento'
        fields = ['cittadino', 'rifiuto', 'quantita'] # Specifica quali campi mostrare nel modulo web (omettiamo operatore e punti, che vengono gestiti in automatico)

class RegistrazioneCittadinoForm(forms.ModelForm): # Crea un modulo per far registrare i nuovi cittadini
    codice_fiscale = forms.CharField(max_length=16, required=True, label="Codice Fiscale") # Aggiunge un campo testuale per il CF, rendendolo obbligatorio (required=True)
    indirizzo = forms.CharField(max_length=255, required=True, label="Indirizzo di Residenza") # Aggiunge un campo testuale per l'indirizzo, obbligatorio

    class Meta: # Istruzioni su come mappare questo modulo al database
        model = User # Il modulo si basa principalmente sulla tabella User standard di Django
        # Campi standard di Django per l'utente base
        fields = ['first_name', 'last_name', 'email', 'password'] # Mostra nome, cognome, email e password
        widgets = { # Personalizza l'aspetto (widget) dei campi nell'HTML
            'password': forms.PasswordInput(), # Fa in modo che il campo password nasconda i caratteri mentre si digita (mostra i pallini neri)
        }

    def clean_codice_fiscale(self): # Metodo speciale di Django che scatta in automatico per "pulire" e validare il campo 'codice_fiscale'
        cf = self.cleaned_data.get('codice_fiscale').upper() # Prende il codice fiscale inserito dall'utente e lo trasforma tutto in MAIUSCOLO
        pattern = r'^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$' # Definisce la regola del CF italiano (6 lettere, 2 numeri, 1 lettera, 2 numeri, 1 lettera, 3 numeri, 1 lettera)
        if not re.match(pattern, cf): # Controlla se il CF inserito rispetta la regola appena scritta
            raise forms.ValidationError("Formato Codice Fiscale non valido.") # Se non la rispetta, blocca il form e mostra questo errore
            
        # Controlliamo che non esista già un CITTADINO con questo CF
        if Cittadino.objects.filter(codice_fiscale=cf).exists(): # Cerca nel DB se c'è già un cittadino con lo stesso CF
            raise forms.ValidationError("Questo Codice Fiscale è già registrato.") # Se c'è già, blocca la registrazione e mostra l'errore
        return cf # Se tutti i controlli sono passati, restituisce il codice fiscale (valido e in maiuscolo) pronto per essere salvato

    def save(self, commit=True): # Sovrascrive il metodo di salvataggio del modulo per fare delle operazioni extra prima di salvare nel DB
        user = super().save(commit=False) # Mette in pausa il salvataggio normale: crea l'oggetto utente in memoria, ma non lo scrive ancora sul database
        user.set_password(self.cleaned_data["password"]) # Cripta la password dell'utente in modo sicuro (Django non salva mai le password in chiaro)
        
        # Cerchiamo l'ID più alto attualmente nel database degli utenti
        max_id = User.objects.aggregate(Max('id'))['id__max'] or 0 # Cerca l'ID più alto nella tabella User. Se la tabella è vuota (None), usa 0
        prossimo_id = max_id + 1 # Calcola quale sarà l'ID del nuovo utente che stiamo creando
        
        # Assegniamo l'ID progressivo (convertito in stringa) come username di Django
        user.username = str(prossimo_id) # Imposta l'username forzandolo ad essere uguale al suo futuro ID (es. username "15")
        user.set_password(self.cleaned_data["password"]) # (Nota: Questa riga ripete il set_password fatto prima, è ridondante ma non causa errori)
        
        if commit: # Se il modulo ci autorizza a scrivere fisicamente nel database (commit=True è il comportamento di default)
            user.save() # Salva l'utente definitivamente nel database
        return user # Restituisce l'utente appena creato alla vista (views.py) che lo aveva richiesto

class TipologiaRifiutoForm(forms.ModelForm): # Crea il modulo per permettere all'admin di aggiungere o modificare un tipo di rifiuto
    class Meta:
        model = TipologiaRifiuto # Lo collega al modello TipologiaRifiuto
        fields = ['nome', 'unita_di_misura', 'punti_per_unita', 'attivo'] # Mostra all'admin questi quattro campi
        labels = { # Personalizza le etichette di testo mostrate sopra ogni campo per renderle più comprensibili a chi compila
            'nome': 'Nome Rifiuto (es. Plastica)',
            'unita_di_misura': 'Unità di Misura (es. Kg, Litri)',
            'punti_per_unita': 'Punti generati per ogni unità',
            'attivo': 'Rifiuto Attivo (disabilita per nasconderlo)'
        }

class ModificaConferimentoForm(forms.ModelForm): # Crea il modulo per l'admin per correggere eventuali errori di peso dei conferimenti
    class Meta:
        model = Conferimento # Lo collega al modello Conferimento
        fields = ['quantita'] # Consente di modificare SOLO la quantità (blocca cittadino, data e operatore per motivi di sicurezza/storico)
        labels = { # Aggiunge un testo descrittivo per spiegare all'admin cosa succederà
            'quantita': 'Correggi la Quantità (I punti del cittadino si aggiorneranno in automatico!)'
        }