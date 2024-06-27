# ruteplan api versjon 3 

Eksempler og div praktiske snutter for kommunikasjon med ruteplantjenesten [https://data.norge.no/data/statens-vegvesen/api-ruteplantjeneste-bil](https://data.norge.no/data/statens-vegvesen/api-ruteplantjeneste-bil)

# Brukernavn og passord

Tilgangskontroll skjer med http basic auth.

Ditt brukernavn og passord legger du inn i filen ```credentials.json```. Via .gitignore-mekanismen unngår du da å publisere passordet ditt på github. Bruk ```credentials-template.json``` som mal. Kontakt [ruteplan@vegvesen.no](ruteplan@vegvesen.no) for å få tilgang. 

# Anropsgrense - 2500 kall per døgn 

Rate limit er 2500 kall per døgn. Så langt har vi ikke trengt å innføre noen streng håndheving av denne grensen. Vær grei, så slipper vi å bli strenge!

Noen problemer, for eksempel mange start- og målpunkt, egner seg dårlig for ruteberegningstjeneste. Hvis du har N startpunkt og M målpunkt trenger du $\frac{N*M}{2}$ ruteberegninger. Dette skalerer ikke når N og M blir store. Se notatene om  [nettverksanalyse](https://github.com/ltglahn/ruteplan/tree/test_fattigmannsnettanalyse).

Vær også oppmerksom på at ruteplantjenesten tilbyr en-til-mange funksjonalitet, se dokumentasjon. 

# Dokumentasjon ruteplan 

Swagger-dokumentasjon https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/open/routingService/openapi/index.html 

# Lenke til ruteplan API 

Lenke til rotnivå for tjenesten (http basic auth) https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/routingService/api

Merk at lenken over ikke fungerer alene: Du må legge til et underliggende endepunkt, for eksempel `/Route/best`. Grunnen er at rotnivå- endepunktet ikke er eksponert mot internett.
