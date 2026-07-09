from django.shortcuts import render, redirect # Importa 'render' per mostrare le pagine HTML e 'redirect' per reindirizzare l'utente su un'altra pagina
from django.contrib.auth.decorators import login_required # Importa un "decoratore" per bloccare l'accesso alle pagine a chi non ha fatto il login
from django.contrib.auth import login # Importa la funzione per far loggare (entrare) automaticamente un utente nel sistema
from django.contrib.admin.views.decorators import staff_member_required # Importa un decoratore per limitare l'accesso solo agli amministratori/staff

# Modelli e Form importati correttamente
from .models import Cittadino, OperatoreEcologico, TipologiaRifiuto, Conferimento, Premio, RichiestaPremio # Importa le tabelle del database (modelli) create nel file models.py
from .forms import ConferimentoForm, RegistrazioneCittadinoForm, TipologiaRifiutoForm, ModificaConferimentoForm # Importa i moduli (form) per gestire l'inserimento dei dati da parte degli utenti

# --- HOMEPAGE ---
def homepage(request): # Definisce la funzione per la pagina principale del sito. 'request' contiene i dati della visita dell'utente
    rifiuti = TipologiaRifiuto.objects.all() # Prende dal database tutte le tipologie di rifiuto disponibili
    return render(request, 'gestione_rifiuti/homepage.html', {'rifiuti': rifiuti}) # Mostra il file HTML della homepage, passandogli la lista dei rifiuti da far vedere a schermo


# --- PUNTO CASSA (Solo Operatori) ---
@login_required(login_url='/login/') # Blocca la pagina: se non sei loggato, ti rimanda alla pagina '/login/'
def punto_cassa(request): # Definisce la pagina dove l'operatore registra i rifiuti portati dai cittadini
    if not hasattr(request.user, 'operatoreecologico'): # Controlla se l'utente attualmente loggato è registrato anche come "Operatore Ecologico"
        return render(request, 'gestione_rifiuti/base.html', { # Se non è un operatore, mostra una pagina generica...
            'content': '<div style="text-align: center; padding: 50px;"><h2>Accesso Negato 🛑</h2><p>Solo gli Operatori Ecologici possono accedere al Punto Cassa.</p></div>' # ...con un messaggio di errore e accesso negato
        })

    operatore = request.user.operatoreecologico # Se i controlli sono passati, salva i dati dell'operatore che sta usando il sito
    rifiuti = TipologiaRifiuto.objects.all() # Prende di nuovo tutte le tipologie di rifiuti per mostrarle nel menu a tendina
    
    if request.method == 'POST': # Controlla se l'utente ha cliccato "Invia" in un modulo (ovvero se sta inviando dati al server)
        cf_cittadino = request.POST.get('cf_cittadino') # Prende dal modulo il codice fiscale inserito dall'operatore
        rifiuto_id = request.POST.get('rifiuto_id') # Prende dal modulo l'ID del tipo di rifiuto selezionato
        quantita = request.POST.get('quantita') # Prende dal modulo la quantità di rifiuti (es. kg o litri) inserita
        
        try: # Inizia un blocco "prova" per gestire eventuali errori (es. se inserisce un codice fiscale inesistente)
            cittadino = Cittadino.objects.get(codice_fiscale=cf_cittadino) # Cerca nel database il cittadino che ha quel preciso codice fiscale
            rifiuto = TipologiaRifiuto.objects.get(id=rifiuto_id) # Cerca nel database il rifiuto selezionato usando il suo ID
            
            Conferimento.objects.create( # Crea e salva nel database un nuovo record di "Conferimento" (la registrazione dei punti)
                cittadino=cittadino, # Associa il cittadino trovato
                operatore=operatore, # Associa l'operatore che sta facendo l'operazione
                rifiuto=rifiuto, # Associa la tipologia di rifiuto
                quantita=quantita # Associa la quantità indicata
            )
            return render(request, 'gestione_rifiuti/punto_cassa.html', { # Ricarica la pagina del punto cassa...
                'rifiuti': rifiuti, # ...rimettendo la lista dei rifiuti...
                'successo': f'Conferimento registrato con successo per {cittadino.utente.first_name}!' # ...e mostrando un messaggio verde di successo con il nome del cittadino
            })
            
        except Cittadino.DoesNotExist: # Se nel blocco 'try' la ricerca del cittadino fallisce (nessun cittadino con quel CF)
            return render(request, 'gestione_rifiuti/punto_cassa.html', { # Ricarica la pagina...
                'rifiuti': rifiuti, # ...mantiene la lista dei rifiuti...
                'errore': 'Cittadino non trovato! Verifica il Codice Fiscale.' # ...e mostra un messaggio di errore rosso
            })

    return render(request, 'gestione_rifiuti/punto_cassa.html', {'rifiuti': rifiuti}) # Se non era una richiesta POST (l'utente ha solo aperto la pagina normalmente), mostra il modulo vuoto


# --- PROFILO CITTADINO ---
@login_required(login_url='/login/') # Protegge la pagina richiedendo il login
def profilo_cittadino(request): # Definisce la pagina personale dove il cittadino vede i suoi punti e la cronologia
    try: # Prova a recuperare i dati
        cittadino = request.user.cittadino # Prende il profilo "Cittadino" collegato all'utente loggato
        storico = Conferimento.objects.filter(cittadino=cittadino).order_by('-data_ora') # Prende tutti i conferimenti di questo cittadino, ordinati per data decrescente (dal più recente)
        errore = None # Se va tutto bene, non ci sono errori da mostrare
    except Cittadino.DoesNotExist: # Se l'utente loggato non ha un profilo Cittadino associato
        cittadino = None # Nessun cittadino da mostrare
        storico = None # Nessuno storico da mostrare
        errore = "Il tuo account non è configurato come cittadino. Contatta il comune." # Imposta il messaggio di errore

    return render(request, 'gestione_rifiuti/profilo_cittadino.html', { # Mostra il file HTML del profilo
        'cittadino': cittadino, # Passa alla pagina i dati del cittadino (nome, punti, ecc.)
        'storico': storico, # Passa la tabella con la cronologia dei rifiuti buttati
        'errore': errore # Passa l'eventuale messaggio di errore
    })


# --- AREA RISCATTO PREMI (CORRETTA) ---
@login_required(login_url='/login/') # Richiede il login per accedere all'area riscatto premi
def area_riscatto(request): # Definisce la pagina dove i cittadini spendono i punti
    try: # Prova a verificare l'identità
        cittadino = request.user.cittadino # Verifica che chi è connesso sia effettivamente un Cittadino
    except Cittadino.DoesNotExist: # Se è, per esempio, un Operatore o un Admin...
        return render(request, 'gestione_rifiuti/base.html', { # ...lo blocca e mostra una pagina di errore generica
            'content': '<div style="text-align: center; padding: 50px;"><h2>Accesso Negato 🛑</h2><p>Questa area è riservata ai cittadini.</p></div>' # Messaggio di blocco
        })

    # CORRETTO: Uso del nuovo campo 'categoria' invece di 'is_tari'
    premi_servizi = Premio.objects.filter(categoria='servizio') # Estrae dal database tutti i premi classificati come "Servizio Pubblico"
    premi_tari = Premio.objects.filter(categoria='tari') # Estrae dal database tutti i premi classificati come "Sconto TARI"
    
    if request.method == 'POST': # Se l'utente ha cliccato il pulsante per richiedere un premio specifico
        premio_id = request.POST.get('premio_id') # Recupera l'ID del premio che l'utente vuole prendere
        premio = Premio.objects.get(id=premio_id) # Cerca le informazioni di quel premio specifico nel database
        
        # CORRETTO: Uso di 'sogliaPunti' invece di 'punti_richiesti'
        if cittadino.saldo_ecopunti < premio.sogliaPunti: # Controlla se i punti posseduti sono MENO di quelli richiesti dal premio
            return render(request, 'gestione_rifiuti/area_riscatto.html', { # In caso affermativo, ricarica la pagina...
                'errore': 'Punti insufficienti per questo premio.', # ...mostrando l'errore "Punti insufficienti"
                'premi_servizi': premi_servizi, # Passa di nuovo i premi per ricaricare la lista
                'premi_tari': premi_tari # Passa di nuovo gli sconti per ricaricare la lista
            })

        # Scaliamo i punti usando il campo aggiornato
        cittadino.saldo_ecopunti -= premio.sogliaPunti # Sottrae i punti del costo del premio dal saldo totale del cittadino
        cittadino.save() # Salva il nuovo saldo aggiornato nel database
        
        RichiestaPremio.objects.create(cittadino=cittadino, premio=premio) # Crea e salva nel DB un "ticket" che segnala che il cittadino ha richiesto questo premio
        return redirect('profilo_cittadino') # Dopo l'acquisto, reindirizza l'utente alla pagina del suo profilo

    return render(request, 'gestione_rifiuti/area_riscatto.html', { # Se l'utente ha solo aperto la pagina, mostra l'HTML
        'premi_servizi': premi_servizi, # Passa la lista dei premi normali per farli vedere a schermo
        'premi_tari': premi_tari # Passa la lista degli sconti Tari
    })


# --- REGISTRAZIONE CITTADINO ---
def registrazione_cittadino(request): # Funzione per la pagina di iscrizione di un nuovo cittadino
    if request.method == 'POST': # Se l'utente ha compilato il form e cliccato "Registrati"
        form = RegistrazioneCittadinoForm(request.POST) # Inserisce i dati inviati dall'utente nell'oggetto form per controllarli
        if form.is_valid(): # Verifica che tutti i campi inseriti rispettino le regole (es. password sicura, CF univoco)
            user = form.save() # Se è tutto valido, salva l'utente base (User di Django, con username e password) nel database
            
            Cittadino.objects.create( # Oltre all'User, crea anche il profilo esteso "Cittadino" collegato
                utente=user, # Lo collega all'User appena creato
                codice_fiscale=form.cleaned_data.get('codice_fiscale'), # Prende il codice fiscale dal form ripulito
                indirizzo=form.cleaned_data.get('indirizzo') # Prende l'indirizzo dal form ripulito
            )
            
            login(request, user) # Effettua automaticamente il login dell'utente appena registrato senza fargli rimettere la password
            return redirect('homepage') # Lo rispedisce alla homepage
    else: # Se l'utente non ha inviato dati ma ha solo aperto la pagina
        form = RegistrazioneCittadinoForm() # Crea un modulo completamente vuoto
        
    return render(request, 'gestione_rifiuti/registrazione.html', {'form': form}) # Mostra la pagina HTML passandogli il modulo (vuoto o con errori se c'erano)


# --- DASHBOARD FRONT-END AMMINISTRATORE ---
@staff_member_required(login_url='/login/') # Protegge la pagina: solo gli account segnati come "Staff" o "Superuser" possono entrare
def dashboard_admin(request): # Funzione per la pagina di gestione lato comune/amministrazione
    rifiuti = TipologiaRifiuto.objects.all() # Recupera la lista di tutti i tipi di rifiuti configurati
    conferimenti = Conferimento.objects.all().order_by('-data_ora')[:30] # Recupera tutti i conferimenti fatti da chiunque, ordinati dal più recente, ma prende SOLO gli ultimi 30
    return render(request, 'gestione_rifiuti/dashboard_admin.html', { # Mostra l'HTML della dashboard
        'rifiuti': rifiuti, # Passa la lista dei rifiuti alla vista
        'conferimenti': conferimenti # Passa gli ultimi 30 movimenti per avere uno storico generale a colpo d'occhio
    })

@staff_member_required(login_url='/login/') # Accesso riservato allo staff
def gestisci_rifiuto(request, pk=None): # Funzione usata SIA per creare un nuovo rifiuto, SIA per modificarne uno esistente (pk = Primary Key)
    rifiuto = TipologiaRifiuto.objects.get(pk=pk) if pk else None # Se l'URL contiene un ID (pk), recupera quel rifiuto. Se non c'è, `rifiuto` diventa None (vuol dire che ne stiamo creando uno nuovo)
    
    if request.method == 'POST': # Se l'admin sta salvando il modulo
        form = TipologiaRifiutoForm(request.POST, instance=rifiuto) # Riempie il modulo con i dati inviati, sovrascrivendo l'oggetto esistente se stiamo modificando
        if form.is_valid(): # Controlla che i dati (nome, punti, ecc.) siano validi
            form.save() # Salva la modifica o la creazione nel database
            return redirect('dashboard_admin') # Torna al pannello di controllo
    else: # Se l'admin ha solo aperto la pagina per vedere il modulo
        form = TipologiaRifiutoForm(instance=rifiuto) # Crea un modulo. Se stiamo modificando, lo pre-compila con i dati vecchi. Se è nuovo, è vuoto
        
    titolo = "Modifica Tipologia Rifiuto" if pk else "Aggiungi Nuova Tipologia Rifiuto" # Sceglie il titolo della pagina dinamicamente
    return render(request, 'gestione_rifiuti/form_admin.html', {'form': form, 'titolo': titolo}) # Mostra il modulo all'admin

@staff_member_required(login_url='/login/') # Accesso riservato allo staff
def modifica_conferimento_admin(request, pk): # Funzione per permettere all'admin di correggere eventuali errori di peso inseriti dall'operatore
    conferimento = Conferimento.objects.get(pk=pk) # Recupera lo specifico conferimento usando il suo ID (Primary Key)
    
    if request.method == 'POST': # Se l'admin preme salva dopo aver corretto i dati
        form = ModificaConferimentoForm(request.POST, instance=conferimento) # Mette i nuovi dati nel modulo, dicendogli di aggiornare l'oggetto specifico
        if form.is_valid(): # Se non ci sono errori (es. lettere al posto di numeri)
            form.save() # Salva la modifica nel DB. (NOTA: questo invocherà in automatico il 'def save()' del modello, che abbiamo commentato prima, ricalcolando la differenza punti in automatico!)
            return redirect('dashboard_admin') # Torna al pannello di controllo
    else: # Se l'admin apre la pagina di modifica
        form = ModificaConferimentoForm(instance=conferimento) # Mostra il modulo pre-compilato con i dati attuali (quelli prima della correzione)
        
    return render(request, 'gestione_rifiuti/form_admin.html', { # Mostra la pagina HTML
        'form': form, # Passa il form da compilare
        'titolo': f"Correzione Errore per: {conferimento.cittadino.utente.last_name}" # Titolo personalizzato che fa capire di chi stiamo modificando l'operazione
    })