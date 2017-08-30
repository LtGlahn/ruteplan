# ruteplan
Eksempler og div praktiske snutter for kommunikasjon med ruteplantjenesten [https://data.norge.no/data/statens-vegvesen/api-ruteplantjeneste-bil](https://data.norge.no/data/statens-vegvesen/api-ruteplantjeneste-bil)

Skrevet i python 3, men har prøvd å være bakoverkompatibel - og prøver så godt jeg kan å dokumentere hva som ikke funker i python 2. 

# Brukernavn og passord

Ditt brukernavn og passord legger du inn i filen ```credentials.json```. Via .gitignore-mekanismen unngår du da å publisere passordet ditt på github. Bruk ```credentials-template.json``` som mal. Kontakt [ruteplan@vegvesen.no](ruteplan@vegvesen.no) for å få tilgang. 


# Fattignmanns nettverkanalyse

En nettverksanalyse består i å analyse reisetider, kostnader og avstander i et nettverk - HELE nettverket betraktet under ett. Dette gjøres typisk i moderne GIS-verktøy. Analysen kan være krevende å sette seg inn og utføre korrekt. 

Fattigmannsvarianten er å bruke ruteplantjenesten med et stort antall start-stopp punkter, f.eks. reiser mellom alle adresser i en liste. Har du N adressepunkt og bare regner den ene retningen (A->B, men ikke B->a) så trenger du (N^2-N)/2 kall til rutekalltjenesten. Du skal ikke ha mer enn 71 punkt i adresselisten din før du er i konflikt med begrensningen på 2500 kall/døgn. 

**SNAKK MED SYSTEMEIER RUTEPLANTJENESTEN HVIS DET ER BEHOV FOR DENNE TYPEN ANALYSER**. [ruteplan@vegvesen.no](ruteplan@vegvesen.no). Så hjelper vi deg med å finne andre løsninger! En variant er at vi kjører denne analysen internt på Vegvesenets datanettverk - mot testmiljøet. Der kan vi kjøre tung belastning uten at det går ut over andre brukere. **SNAKK MED OSS**, så finner vi løsninger! 

