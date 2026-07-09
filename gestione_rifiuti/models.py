import uuid # Importa la libreria 'uuid' di Python per generare identificatori univoci (anche se in questo file non viene poi usata)
from django.db import models # Importa il modulo 'models' di Django, che contiene gli strumenti per creare le tabelle del database
from django.contrib.auth.models import User # Importa il modello standard 'User' di Django, usato per gestire autenticazione, login e password

class Cittadino(models.Model): # Definisce una nuova tabella nel database chiamata "Cittadino"
    utente = models.OneToOneField(User, on_delete=models.CASCADE) # Crea una relazione 1-a-1: ogni cittadino è collegato a un singolo account User. Se l'User viene cancellato (CASCADE), si cancella anche il Cittadino
    codice_fiscale = models.CharField(max_length=16, unique=True) # Crea una colonna di testo per il codice fiscale, massimo 16 caratteri. 'unique=True' impedisce codici fiscali duplicati nel DB
    indirizzo = models.CharField(max_length=255) # Crea una colonna di testo per l'indirizzo dell'utente, massimo 255 caratteri
    saldo_ecopunti = models.IntegerField(default=0) # Crea una colonna numerica (numeri interi) per registrare i punti; parte da 0 di default

    def __str__(self): # Metodo speciale di Python che decide come questo oggetto verrà mostrato in forma testuale (es. nel pannello di amministrazione)
        return f"{self.utente.last_name} ({self.codice_fiscale})" # Restituisce una stringa contenente il cognome dell'utente e il suo codice fiscale tra parentesi

class OperatoreEcologico(models.Model): # Definisce una nuova tabella nel database chiamata "OperatoreEcologico"
    utente = models.OneToOneField(User, on_delete=models.CASCADE) # Associa l'operatore a un account User standard (relazione 1-a-1, se cancelli l'User si cancella l'Operatore)
    codice_fiscale = models.CharField(max_length=16, unique=True) # Colonna di testo per il codice fiscale, univoco, max 16 caratteri
    codice_identificativo = models.CharField(max_length=50, unique=True) # Colonna di testo univoca per un ID aziendale interno dell'operatore (es. matricola)

    def __str__(self): # Metodo per la visualizzazione testuale dell'oggetto
        return f"Operatore {self.codice_identificativo} - {self.utente.last_name}" # Mostra la scritta "Operatore [matricola] - [cognome]"

class TipologiaRifiuto(models.Model): # Definisce una tabella che mappa i tipi di rifiuto (es. Plastica, Vetro, Carta)
    nome = models.CharField(max_length=100) # Colonna di testo per il nome della tipologia di rifiuto, massimo 100 caratteri
    unita_di_misura = models.CharField(max_length=10) # Colonna di testo per indicare l'unità (es. "kg", "litri", "pezzi")
    # mantieni i parametri originali del tuo DecimalField per punti_per_unita
    punti_per_unita = models.DecimalField(max_digits=10, decimal_places=2) # Colonna decimale: indica quanti punti vale 1 unità di questo rifiuto (fino a 10 cifre totali, di cui 2 decimali)
    attivo = models.BooleanField(default=True)  # <-- AGGIUNTO # Colonna VERO/FALSO per disabilitare vecchie tipologie di rifiuti senza cancellarle dal DB. Default VERO.

    def __str__(self): # Metodo per la visualizzazione testuale
        return self.nome # Mostra semplicemente il nome del rifiuto

class Conferimento(models.Model): # Tabella che registra ogni singola volta che un cittadino butta la spazzatura accumulando punti
    data_ora = models.DateTimeField(auto_now_add=True) # Salva in automatico la data e l'ora esatta in cui questo record viene creato
    cittadino = models.ForeignKey(Cittadino, on_delete=models.CASCADE) # Collega il conferimento al cittadino che lo ha fatto (se elimini il cittadino, elimini i suoi conferimenti)
    operatore = models.ForeignKey(OperatoreEcologico, on_delete=models.SET_NULL, null=True, blank=True) # <-- Aggiunto # Collega il conferimento all'operatore. Se l'operatore viene licenziato/cancellato, questo campo diventa nullo (SET_NULL) per non perdere lo storico
    rifiuto = models.ForeignKey(TipologiaRifiuto, on_delete=models.RESTRICT) # Collega il conferimento al tipo di spazzatura. RESTRICT impedisce di cancellare una TipologiaRifiuto se è già stata usata in un conferimento
    quantita = models.DecimalField(max_digits=8, decimal_places=2) # Quantità effettivamente conferita dal cittadino (fino a 8 cifre e 2 decimali)
    punti_generati = models.IntegerField(blank=True, null=True) # Punti guadagnati con questo specifico conferimento. Può essere lasciato vuoto perché lo calcoliamo noi dopo

    def save(self, *args, **kwargs): # Sovrascrive il metodo di salvataggio standard di Django per aggiungere logica automatica
        nuovi_punti = int(float(self.quantita) * float(self.rifiuto.punti_per_unita)) # Calcola i punti moltiplicando quantità x valore unitario, poi converte il risultato in numero intero
        
        if self.pk: # Controlla se 'self.pk' (Primary Key) esiste già. Se esiste, stiamo modificando un conferimento esistente, non creandone uno nuovo
            vecchio = Conferimento.objects.get(pk=self.pk) # Prende dal database i vecchi dati di questo stesso conferimento
            delta_punti = nuovi_punti - (vecchio.punti_generati or 0) # Calcola la differenza tra i punti ricalcolati ora e quelli che aveva in precedenza
            self.cittadino.saldo_ecopunti += delta_punti # Aggiorna il portafoglio del cittadino aggiungendo o togliendo solo la differenza
        else: # Se la Primary Key non c'è, significa che stiamo creando questo record per la prima volta
            self.cittadino.saldo_ecopunti += nuovi_punti # Aggiunge direttamente tutti i nuovi punti calcolati al totale del cittadino
            
        self.punti_generati = nuovi_punti # Salva nel database (nella riga di questo conferimento) i punti appena calcolati
        self.cittadino.save() # Salva il nuovo saldo del cittadino nel database
        super().save(*args, **kwargs) # Esegue il vero e proprio comando di salvataggio del conferimento (quello standard di Django che avevamo messo in pausa)

class Premio(models.Model): # Definisce la tabella per i premi o gli sconti riscattabili
    nome = models.CharField(max_length=100) # Colonna di testo per il nome del premio
    descrizione = models.TextField(blank=True, null=True)  # <-- AGGIUNTO # Colonna di testo lungo per descrivere il premio (opzionale, può essere vuota)
    sogliaPunti = models.IntegerField()  # <-- RINOMINATO (era punti_richiesti) # Colonna numerica (intera) per indicare quanti punti servono per riscattare questo premio
    
    # MODIFICATO: Sostituisce 'is_tari'. Usa scelte per mappare i valori in modo pulito
    CATEGORIA_CHOICES = [ # Crea una lista fissa di categorie possibili per i premi (evita errori di battitura nel database)
        ('tari', 'Sconto TARI'), # Primo valore: 'tari' è salvato nel database, 'Sconto TARI' è mostrato all'utente
        ('servizio', 'Servizio Pubblico') # Secondo valore: 'servizio' salvato nel DB, 'Servizio Pubblico' mostrato all'utente
    ]
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default='servizio') # Colonna per la categoria, limitata alle scelte sopra. Default su 'servizio'
    
    attivo = models.BooleanField(default=True)  # <-- AGGIUNTO # Campo VERO/FALSO per poter "ritirare" un premio dal catalogo senza cancellarlo
    icona = models.CharField(max_length=10, default="🎁") # Colonna per un'emoji, di default il pacco regalo

    def __str__(self): # Metodo per la visualizzazione testuale
        return f"{self.icona} {self.nome} ({self.sogliaPunti} pt)" # Mostra l'icona, il nome e i punti necessari, es: "🎁 Sconto Tari (500 pt)"

class RichiestaPremio(models.Model): # Tabella che registra ogni volta che un cittadino usa i punti per comprare un premio
    STATO_CHOICES = [ # Definisce gli stati in cui può trovarsi la pratica
        ('in_attesa', 'In Attesa'), # Il cittadino ha chiesto il premio ma non è stato ancora erogato
        ('processato', 'Processato (Flusso Generato)'), # La richiesta è stata approvata/chiusa
    ]
    cittadino = models.ForeignKey('Cittadino', on_delete=models.CASCADE) # Collega la richiesta al cittadino (se elimini il cittadino, si elimina la richiesta)
    premio = models.ForeignKey(Premio, on_delete=models.CASCADE) # Collega la richiesta al premio desiderato
    
    # ... mantieni qui gli eventuali altri campi che avevi (es. data, stato ecc.)
    data = models.DateTimeField(auto_now_add=True) # Salva in automatico data e ora in cui viene fatta la richiesta del premio
    stato = models.CharField(max_length=20, choices=STATO_CHOICES, default='in_attesa') # Colonna per lo stato della pratica, limitato alle due scelte in alto. Parte da "in_attesa"

    def __str__(self): # Metodo per la visualizzazione testuale
        return f"Richiesta {self.premio.nome} di {self.cittadino}" # Mostra una sintesi: "Richiesta [Nome Premio] di [Nome Cittadino]"