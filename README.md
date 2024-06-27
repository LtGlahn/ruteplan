# Oppdatering til versjon 3 av ruteplan API 

Denne koden utvikles til å hente data fra versjon 3 av ruteplan API. Den vil erstatte master-branch når tiden er moden for det. 

# ruteplan
Eksempler og div praktiske snutter for kommunikasjon med ruteplantjenesten [https://data.norge.no/data/statens-vegvesen/api-ruteplantjeneste-bil](https://data.norge.no/data/statens-vegvesen/api-ruteplantjeneste-bil)

# Brukernavn og passord

Tilgangskontroll skjer med http basic auth.

Ditt brukernavn og passord legger du inn i filen ```credentials.json```. Via .gitignore-mekanismen unngår du da å publisere passordet ditt på github. Bruk ```credentials-template.json``` som mal. Kontakt [ruteplan@vegvesen.no](ruteplan@vegvesen.no) for å få tilgang. 

# Anropsgrense - 2500 kall per døgn 

Rate limit er 2500 kall per døgn. Så langt har vi ikke trengt å innføre noen streng håndheving av denne grensen. Vær grei, så slipper vi å bli strenge!

Noen problemer, for eksempel mange start- og målpunkt, egner seg dårlig for ruteberegningstjeneste. Hvis du har N startpunkt og M målpunkt trenger du $\frac{N*M}{2}$ ruteberegninger. Dette skalerer ikke når N og M blir store. Se notatene om  [nettverksanalyse](https://github.com/ltglahn/ruteplan/tree/test_fattigmannsnettanalyse).

# Dokumentasjon ruteplan 

Etter hvert vil vi ha en beskrivelse av ruteplantjenesten V3 inklusive swagger-dokumentasjon samme sted som vi dokumenterer våre øvrige NVDB-produkter https://nvdb.atlas.vegvesen.no. I mellomtiden har vi publisert swagger-dokument på https://labs.vegdata.no/ruteplandoc/

Ruteplan versjon 2 er dokumentert på https://labs.vegdata.no/ruteplandoc/ruteplandoc_v2.html 