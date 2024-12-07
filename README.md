# Multi DEX Solana Trading Bot (Dimostrativo)

Questo progetto fornisce un esempio di un bot di trading automatico su Solana DEX (Serum) con supporto a più mercati contemporaneamente. Include:

- Raccolta dati in tempo reale dagli order book di diversi DEX/market.
- Modello di Machine Learning (caricato da file `model.h5` se presente) per predizioni di prezzo.
- Logica di trading automatica (buy/sell/hold) basata sulle predizioni.
- Heuristics per rug pull detection (spread elevato, basso volume, crollo prezzo).
- Interfaccia grafica con PyQt5 e matplotlib, una tab per ogni DEX con grafici, log e dati live.
- Codice modulare e commentato.

## Prerequisiti

- Python 3.8+  
- Installare le dipendenze:  
  ```bash
  pip install pyqt5 pyserum solana tensorflow keras-tuner matplotlib

Il bot, così come è stato presentato nei file completi, segue una logica di funzionamento a più livelli, dalla raccolta dati fino al piazzamento degli ordini, passando per la GUI e il modello di machine learning. Ecco un riassunto dei passaggi, step-by-step:

Avvio e Configurazione

Quando lanci main.py, il programma carica le configurazioni dal file config.py.
In config.py ci sono la lista dei DEX (endpoint, indirizzo del market, chiave privata, valute), i parametri di trading (HISTORY_LENGTH, ORDER_SIZE, ecc.) e i parametri per il modello ML.
Viene avviata l’applicazione PyQt5 per la GUI (MainWindow in ui.py).
Creazione dei Worker per i DEX

Per ogni DEX definito in DEX_CONFIGS, il main crea un’istanza di TradingBotWorker (definito in bot.py).
Ogni TradingBotWorker è responsabile di un singolo DEX/market. Ha la sua chiave privata, endpoint, market address, e manterrà una serie di dati interni (data_buffer) per il machine learning e la logica di trading.
Esecuzione Asincrona

Il main avvia un event loop asyncio in un thread separato.
All’interno di questo event loop, vengono eseguiti in parallelo tutti i TradingBotWorker tramite la coroutine run_bot().
Fetch dei Dati di Mercato

Ogni worker (TradingBotWorker), all’interno del proprio loop (while self.running: in run_bot()), chiama periodicamente fetch_market_data() (definito in utils.py).
fetch_market_data() si collega al DEX usando pyserum e solana, legge order book (bid, ask) e calcola parametri come mid_price, spread, volume. Se non trova dati, emette un warning e riprova dopo qualche secondo.
Accumulo dei Dati e Preprocessing

I dati ottenuti vengono trasformati in un array di feature (mid_price, spread, volume) e aggiunti a data_buffer.
Quando data_buffer è sufficientemente lungo (più di HISTORY_LENGTH + FUTURE_STEPS), il bot può allenare o aggiornare il modello ML e generare predizioni.
Modello di Machine Learning

Il modello ML (in ml_model.py) è un LSTM semplice che predice se il prezzo salirà o no dopo un certo numero di step (FUTURE_STEPS).
Alla prima esecuzione, il modello prova a caricare model.h5 (modello pre-addestrato). Se non lo trova, crea un modello baseline.
Ad ogni ciclo, quando ci sono abbastanza dati, il modello viene aggiornato in modo incrementale (train_model()) con gli ultimi batch di dati.
Quindi il bot fa una predizione (predict()) sullo stato attuale. La predizione è un valore tra 0 e 1 (ad es. >0.7 significa alta probabilità di rialzo).
Logica di Trading

In base alla predizione, il bot decide:
Pred > 0.7: acquista una piccola quantità (ORDER_SIZE) del token base.
Pred < 0.3: se ha una posizione aperta (posizioni long accumulate), vende una piccola quantità.
Altrimenti, non fa nulla (HOLD).
Prima di eseguire un trade, controlla se c’è un rischio di rug pull (check_rug_pull() in utils.py) verificando spread troppo elevato, volume basso, crollo del prezzo. In caso di pericolo, se ha posizioni aperte, vende tutto subito (emergency sell).
Gli ordini vengono inviati con place_order() che si interfaccia con Serum. Qui è necessario avere la giusta chiave privata e avere fondi disponibili sul proprio account.
Aggiornamento GUI e Log

Ogni worker emette segnali PyQt5 (data_signal, log_signal, chart_signal) per aggiornare l’interfaccia.
La GUI (ui.py) ha un tab per ogni DEX, dove mostra:
Ultimo prezzo, spread, predizione
Un log di eventi (es. ordini piazzati, allarmi rug pull, ecc.)
Un grafico con l’andamento del mid_price nel tempo.
L’utente vede in tempo reale l’evoluzione dei dati e delle decisioni del bot.
Stop e Chiusura

Se l’utente clicca su “Stop”, viene inviato un segnale a tutti i worker (bw.stop()), che smettono di fetchare dati e di piazzare ordini.
Quando tutti i worker finiscono, l’applicazione si chiude.
Riepilogo Logico:

Inizia: Lancia main.py.
Crea GUI e Worker: Per ogni DEX crea un worker.
Ciclo del Worker:
Fetch dati → Aggiorna dataset → Se abbastanza dati → Allena modello → Predici → Decidi trade (Buy, Sell, Hold, o Emergency Sell) → Invia segnali GUI e log → attende qualche secondo e ripete.
Interrompere: Clic su stop → worker si fermano → chiusura app.
In sintesi, questo bot alterna fasi di raccolta dati (fetch), elaborazione ML (train e predict), decisioni di trading e output su GUI. L’intero ciclo è asincrono, con più DEX in parallelo, ognuno con il proprio flusso.

python fetch_historical_data.py --market <MARKET_ADDRESS> --start YYYY-MM-DD --end YYYY-MM-DD
python tune_model.py
python main.py
