# Oppdatering til versjon 3 av ruteplan API 

Denne koden utvikles til å hente data fra versjon 3 av ruteplan API. Den vil erstatte master-branch når tiden er moden for det. 

# ruteplan
Eksempler og div praktiske snutter for kommunikasjon med ruteplantjenesten [https://data.norge.no/data/statens-vegvesen/api-ruteplantjeneste-bil](https://data.norge.no/data/statens-vegvesen/api-ruteplantjeneste-bil)

Skrevet i python 3, men har prøvd å være bakoverkompatibel - og prøver så godt jeg kan å dokumentere hva som ikke funker i python 2. 

# Brukernavn og passord

Ditt brukernavn og passord legger du inn i filen ```credentials.json```. Via .gitignore-mekanismen unngår du da å publisere passordet ditt på github. Bruk ```credentials-template.json``` som mal. Kontakt [ruteplan@vegvesen.no](ruteplan@vegvesen.no) for å få tilgang. 

# Dokumentasjon ruteplan 

Etter hvert vil vi ha en beskrivelse av ruteplantjenesten V3 inklusive swagger-dokumentasjon samme sted som vi dokumenterer våre øvrige NVDB-produkter https://nvdb.atlas.vegvesen.no. I mellomtiden har vi publisert swagger-dokument på https://labs.vegdata.no/ruteplandoc/

Ruteplan versjon 2 er dokumentert på https://labs.vegdata.no/ruteplandoc/ruteplandoc_v2.html 