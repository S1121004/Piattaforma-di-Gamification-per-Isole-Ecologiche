from django.contrib import admin # Importa il modulo 'admin' di Django, necessario per creare e configurare il pannello di controllo
from django.http import HttpResponse # Importa HttpResponse, che serve per restituire al browser file (come il CSV) al posto delle classiche pagine web
import csv # Importa la libreria standard di Python per creare, leggere e scrivere file in formato CSV (fogli di calcolo testuali)
from .models import Cittadino, OperatoreEcologico, TipologiaRifiuto, Conferimento, Premio, RichiestaPremio # Importa i tuoi modelli dal file models.py

@admin.register(OperatoreEcologico) # Decoratore che dice a Django: "Collega la classe qui sotto al modello OperatoreEcologico nel pannello admin"
class OperatoreAdmin(admin.ModelAdmin): # Definisce come deve apparire la pagina di gestione degli Operatori Ecologici
    list_display = ('codice_identificativo', 'codice_fiscale', 'get_nome', 'get_cognome') # Imposta le colonne da mostrare nella tabella: ID operatore, CF, e i campi calcolati nome e cognome
    search_fields = ('codice_identificativo', 'codice_fiscale') # Aggiunge una barra di ricerca che permette di cercare gli operatori per ID o per Codice Fiscale
    
    def get_nome(self, obj): return obj.utente.first_name # Funzione personalizzata per estrarre il nome di battesimo dall'account "User" collegato all'operatore
    def get_cognome(self, obj): return obj.utente.last_name # Funzione personalizzata per estrarre il cognome dall'account "User" collegato

@admin.register(Cittadino) # Collega questa configurazione al modello Cittadino
class CittadinoAdmin(admin.ModelAdmin): # Definisce la gestione dei cittadini nel pannello admin
    # RIMOSSA la tessera_sanitaria
    list_display = ('codice_fiscale', 'get_nome', 'get_cognome', 'saldo_ecopunti') # Imposta le colonne della tabella: CF, nome, cognome e i punti attuali
    search_fields = ('codice_fiscale', 'utente__first_name', 'utente__last_name', 'utente__email') # Permette all'admin di cercare un cittadino scrivendo CF, nome, cognome o email
    list_filter = ('saldo_ecopunti',) # Aggiunge un pannello laterale per filtrare i cittadini in base ai punti (es. per vedere chi ha 0 punti)

    def get_nome(self, obj): return obj.utente.first_name # Estrae il nome dal modello User
    get_nome.short_description = 'Nome' # Cambia il titolo della colonna nella tabella del pannello da "Get nome" a "Nome"

    def get_cognome(self, obj): return obj.utente.last_name # Estrae il cognome dal modello User
    get_cognome.short_description = 'Cognome' # Cambia il titolo della colonna in "Cognome"

@admin.register(TipologiaRifiuto) # Collega la configurazione al modello TipologiaRifiuto
class TipologiaRifiutoAdmin(admin.ModelAdmin): # Definisce la schermata di gestione dei tipi di spazzatura
    # AGGIUNTO 'attivo'
    list_display = ('nome', 'punti_per_unita', 'unita_di_misura', 'attivo') # Mostra nella tabella il nome del rifiuto, i punti che vale, l'unità e se è attualmente attivo
    list_filter = ('attivo',) # Crea un filtro laterale per vedere velocemente solo i rifiuti attivi o solo quelli disattivati
    search_fields = ('nome',) # Permette di cercare una tipologia di rifiuto dal nome

@admin.register(Conferimento) # Collega la configurazione allo storico dei Conferimenti
class ConferimentoAdmin(admin.ModelAdmin): # Definisce la schermata di visualizzazione di tutti i rifiuti buttati
    list_display = ('data_ora', 'cittadino', 'rifiuto', 'quantita', 'punti_generati') # Colonne: data e ora, chi l'ha buttato, cosa, quanto e i punti guadagnati
    list_filter = ('rifiuto', 'data_ora') # Filtri laterali: permette di filtrare le operazioni per tipo di rifiuto o per periodo (es. "questo mese")
    search_fields = ('cittadino__codice_fiscale',) # Permette di cercare tutti i conferimenti di una specifica persona usando il suo CF

@admin.register(Premio) # Collega la configurazione al catalogo dei Premi
class PremioAdmin(admin.ModelAdmin): # Gestione del catalogo premi
    # AGGIORNATO con sogliaPunti, attivo e categoria
    list_display = ('icona', 'nome', 'sogliaPunti', 'get_tipo_premio', 'attivo') # Colonne: icona, nome, punti necessari, il tipo formattato e se è attivo
    list_filter = ('categoria', 'attivo') # Filtri laterali per vedere solo gli Sconti Tari, solo i Servizi, o solo i premi disattivati
    search_fields = ('nome', 'descrizione') # Permette la ricerca per nome del premio o per una parola chiave nella descrizione

    def get_tipo_premio(self, obj): # Crea una funzione per mostrare la categoria in modo più bello graficamente
        return "🏷️ Sconto TARI" if obj.categoria == 'tari' else "🎫 Servizio Pubblico" # Restituisce una stringa con emoji a seconda del valore nel DB
    get_tipo_premio.short_description = 'Categoria' # Intitola la colonna "Categoria" invece del nome della funzione


# GENERAZIONE FLUSSO TARI (RF20 / UC22)
@admin.action(description='Genera Flusso TARI (CSV) per i selezionati') # Trasforma questa funzione in una "Azione di massa" selezionabile dal menu a tendina dell'admin
def esporta_flusso_tari(modeladmin, request, queryset): # queryset contiene tutte le richieste che l'admin ha "spuntato" con la casella di controllo
    response = HttpResponse(content_type='text/csv') # Crea una risposta HTTP speciale dicendo al browser: "Preparati, ti sto mandando un file CSV, non una pagina web"
    response['Content-Disposition'] = 'attachment; filename="flusso_tari_tributi.csv"' # Ordina al browser di scaricare il file e gli assegna il nome "flusso_tari_tributi.csv"
    
    writer = csv.writer(response, delimiter=';') # Prepara un "pennarello virtuale" (writer) per scrivere nel CSV, impostando il punto e virgola come separatore tra le colonne
    # RIMOSSA tessera sanitaria dalle colonne del CSV
    writer.writerow(['Nome', 'Cognome', 'Codice Fiscale', 'Premio Richiesto', 'Data Richiesta']) # Scrive la primissima riga del file, ovvero le intestazioni delle colonne
    
    for richiesta in queryset: # Inizia un ciclo (loop) su ogni singola richiesta che l'admin aveva selezionato
        c = richiesta.cittadino # Salva il cittadino relativo a questa specifica richiesta nella variabile "c" per comodità
        writer.writerow([c.utente.first_name, c.utente.last_name, c.codice_fiscale, richiesta.premio.nome, richiesta.data.strftime("%d/%m/%Y")]) # Scrive una nuova riga nel CSV con i dati reali. strftime converte la data nel formato Giorno/Mese/Anno
        richiesta.stato = 'processato' # Cambia lo stato in automatico! (sposta la pratica da "In Attesa" a "Processato")
        richiesta.save() # Salva nel database il cambio di stato appena effettuato
        
    return response # Invia il file CSV completato al browser dell'amministratore, facendo partire il download

# RINOMINATO in RichiestaPremioAdmin (registra RichiestaPremio anziché Riscatto)
@admin.register(RichiestaPremio) # Collega la gestione delle RichiestePremio al pannello admin
class RichiestaPremioAdmin(admin.ModelAdmin): # Definisce come mostrare l'elenco di chi ha richiesto un premio
    list_display = ('cittadino', 'premio', 'data', 'stato') # Colonne: chi lo chiede, cosa chiede, quando e a che punto è la pratica
    # AGGIORNATO il filtro per usare 'categoria' anziché 'is_tari'
    list_filter = ('stato', 'premio__categoria') # Filtri laterali: permette all'admin di vedere "Tutte le pratiche in attesa" o "Tutte le richieste di sconto Tari"
    actions = [esporta_flusso_tari] # Aggiunge nel menu a tendina in alto ("Azione") il nostro script automatico per esportare i dati in CSV