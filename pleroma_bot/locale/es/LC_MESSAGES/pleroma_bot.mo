��    h      \  �   �      �  �   �  8   �	  (   �	  `   
  /   t
  �   �
  V   1  4   �  9   �  �   �  h   �       /   9  W   i  #   �  #   �  O   	  G   Y     �     �     �     �            �   2  d   �  �     <   �  (   �       \        x     �      �  @   �  %     0   +  '   \  *   �  Q   �       2        K  d   b  c   �  3   +  p   _  \   �  C   -  T   q  ,   �  4   �  3   (  ;   \  -   �  P   �          (     <  1   P     �     �     �     �  /   �  D     N   H  F   �  A   �        F   6     }  Q   �  V   �     :  U   Y  "   �  I   �  	     I   &  I   p  �   �     �     �     �  0   �  9   �     4  9   D    ~  6   �  /   �  n   �  }   j  �   �  j   y   A   �   _   &!  S   �!     �!     �!     "     "  �  3"    �#  S   �$  9   F%  e   �%  2   �%  �   &  i   �&  Q   $'  B   v'  �   �'  �   �(      4)  9   U)  {   �)  '   *  &   3*  `   Z*  F   �*  !   +     $+     C+     Z+  %   w+     �+  �   �+  x   d,  �   �,  G   �-  9   �-     .  ^   %.     �.     �.  ;   �.  I   �.  "   9/  9   \/  =   �/  0   �/  P   0     V0  8   q0     �0  f   �0  k   +1  9   �1  �   �1  }   l2  U   �2  x   @3  ;   �3  N   �3  =   D4  =   �4  >   �4  ^   �4     ^5     o5     �5  C   �5     �5     �5     6     *6  /   A6  X   q6  `   �6  X   +7  ;   �7     �7  F   �7     8  a   58  e   �8  $   �8  e   "9  B   �9  _   �9     +:  K   =:  L   �:  �   �:     �;     �;     �;  :   <  <   B<     <  B   �<  r  �<  A   P>  0   �>  v   �>  �   :?  �   �?  �   {@  I   A  p   YA  r   �A  /   =B     mB     �B     �B     E   K   -       7   C   0   2   X       R   5       ,   L                     G   P       *   ;   1   (      3       )              	   ]      `   D   :      $         "      +   ^   ?   6         8   a       V          I   A   9      '       c       f      B         W       #   F   J          g   d       %   4             !       H   e           N      .       b                          O   M   >   <   _       [   Z       h                        \       U       T      /   Y   =   Q   S              @         
   &    

In order to generate a config file, some information will be needed.

What do you want to use with the bot?
1. Twitter archive
2. RSS feed
3. Guest tokens (no required developer account)
4. Twitter tokens
Select an option (1-4):  

No config found at {}
Do you want to create one? (Y/n) 

Please input the RSS URL to use [rss]: 

Please input the URL of your Fediverse instance (Pleroma/Mastodon/Misskey) [pleroma_base_url]: 

Please input the path to your archive (.zip): 

Please input the username (or account ID if using Mastodon) of the Fediverse account
to use as a target when mirroring [pleroma_username]: 

Please input the username of the Twitter user you want to mirror [twitter_username]: 

Please input your Fediverse token [pleroma_token]: 

Please input your Twitter Bearer token [twitter_token]: 
Enter a date (YYYY-MM-DD):
[Leave it empty to retrieve *ALL* tweets or enter 'continue'
if you want the bot to execute as normal (checking date of 
last post in the Fediverse account)]  
Using RSS feed. The following features will not be available: 
- Profile update
- Pinned tweets
- Polls API version not supported: {} Attachment exceeded config file size limit ({}) Attachments: {}. Media attachment limit for target instance is {}. Ignoring the rest... Attempting to acquire lock {} on {} Attempting to release lock {} on {} Bot flag in target profile ({}) differs from your config. Updating it to {}...  Bot for mirroring one or multiple Twitter accounts in Pleroma/Mastodon. Couldn't expand the url {}: {} Couldn't expand the url: {} Current pinned:	{} Debug logging enabled Error uploading media:	{} Exception occurred Exception occurred
Error code 422
(Unprocessable Entity)
Please check that the bio text or the metadata fields text
aren't too long. Exception occurred
Media not found (404)
{tweet} - {media_url}
Ignoring attachment and continuing... Exception occurred
Media size too large:
Filename: {file}
Size: {size}MB
Consider increasing the attachment
 size limit of your instance Exception occurred
Unprocessable Entity
{error}
File: {file} Exception occurred for user, skipping... File size: {}MB File with previous pinned post ID not found or empty. Checking last posts for pinned post... Gathering tweets...  Gathering tweets...{} Giving up, reference is too deep How far back should we retrieve tweets from the Twitter account? Ignoring attachment and continuing... Instance appears to be Misskey ฅ^•ﻌ•^ฅ Instance response was not understood {} Invalid forceDate format, use "YYYY-mm-dd" It seems like pleroma-bot is running for the first time for this Twitter user: {} Lock {} acquired on {} Lock {} not acquired on {}, waiting {} seconds ... Lock {} released on {} Mastodon cannot attach a video to a post that already contains images, skipping video attachment...  Mastodon doesn't support display names longer than 30 characters, truncating it and trying again... Mastodon doesn't support rich text. Disabling it... Mastodon only supports {} video/s per post, with no mixed media.Already reached max media, skipping the rest...  Mastodon only supports {} video/s per post. Already reached max media, skipping the rest...  Media possibly geoblocked? (403) Skipping... {tweet} - {media_url}  Multiple twitter users for one Fediverse account, skipping profile and pinned tweet. Multiple twitter users, not updating profile No Pleroma URL defined in config! [pleroma_base_url] No posts were found in the target Fediverse account Not enough posts were found in the target Fediverse account Pinned post not found. Giving up unpinning... Pinned post {} not found. Was it deleted? Checking last posts for pinned post... Pinning post:	{} Post in Misskey:	{} Post in Pleroma:	{} Post text longer than allowed ({}), truncating... Posting tweets...  Previous pinned:	{} Processing tweets...  Processing user:	{} Raising max_tweets to the maximum allowed value Rate limit exceeded when getting guest token. Retrying with a proxy. Rate limit exceeded when using a guest token. Refreshing token and retrying... Rate limit exceeded when using a guest token. Retrying with a proxy... Rate limit exceeded. {} out of {} requests remaining until {} UTC Reblog in Pleroma:	{} Received HTTP 404 when trying to get tweet. Tweet deleted? Skipping... Sleeping for {}s... Software on target instance ({}) not recognized. Falling back to Pleroma-like API Some or all OAuth 1.0a tokens missing, falling back to application-only authentication Target instance is Mastodon... The file lock '{}' could not be acquired. Is another instance of pleroma-bot running? Timeout on acquiring lock {} on {} Total number of metadata fields cannot exceed 4.
Provided: {}. Exiting... Trying {} Tweet already posted in Misskey:	{} - {}. Skipping to avoid duplicates... Tweet already posted in Pleroma:	{} - {}. Skipping to avoid duplicates... Unable to retrieve tweets. Is the account protected? If so, you need to provide the following OAuth 1.0a fields in the user config:
 - consumer_key 
 - consumer_secret 
 - access_token_key 
 - access_token_secret Unpinned: {} Unpinning previous:	{} Updating profile:	 {} Visibility not supported! Values allowed are: {} application_name won't work for Misskey ฅ^ዋ⋏ዋ^ฅ config path: {} filter pleroma posts with application name {}, length: {} forces the tweet retrieval to start from a specific date. The twitter_username value (FORCEDATE) can be supplied to only force it for that particular user in the config. Instead of the twitter_username a date (YYYY-MM-DD) can also be supplied to force that date for *all* users max_tweets must be between 10 and 3200. max_tweets: {} number of threads to use when processing tweets only applies to daemon mode. How often to run the program in the background (in minutes). By default is 60min. path of config file (config.yml) to use and parse. If not specified, it will try to find it in the current working directory. path of lock file (pleroma_bot.lock) to prevent collisions  with multiple bot instances. By default it will be placed  next to your config file. path of log file (error.log) to create. If not specified, it will try to store it at your config file path path of the Twitter archive file (zip) to use for posting tweets. run in daemon mode. By default it will re-run every 60min. You can control this with --pollrate skips Fediverse profile update (no background image, profile image, bio text, etc.) skips first run checks tweets gathered: 	 {} tweets temp folder: {} tweets to post: 	 {} Project-Id-Version: pleroma-bot
PO-Revision-Date: 2022-12-26 21:29+0100
Last-Translator: robertoszek <robertoszek@robertoszek.xyz>
Language-Team: 
Language: es
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=2; plural=(n != 1);
Generated-By: pygettext.py 1.5
X-Generator: Poedit 3.2.2
X-Poedit-Basepath: ../../..
X-Poedit-SearchPath-0: .
X-Poedit-SearchPathExcluded-0: tests
 

Para generar un archivo de configuración, cierta información es necesaria.

¿Qué quieres usar con el bot?
1. Archivo de Twitter
2. Canal RSS
3. Tokens de invitado (no se necesita cuenta de desarrollador)
4. Tokens de Twitter
Selecciona una opción (1-4):  

No se ha encontrado un archivo de configuración en {}
¿Quieres crear uno? (Y/n) 

Por favor introduzca la URL del canal RSS a usar [rss]: 

Por favor introduzca la URL de la instancia objetivo (Pleroma/Mastodon/Misskey) [pleroma_base_url]: 

Por favor introduzca la ruta del archivo (.zip): 

Por favor introduzca el nombre del usuario (ó el ID de cuenta si usa Mastodon) de la cuenta de Fediverso
a usar como objetivo al replicar [pleroma_username]: 

Por favor introduzca el nombre de usuario del usuario de Twitter que desea replicar [twitter_username]: 

Por favor introduzca el Bearer token de la cuenta de Fediverso [pleroma_token]: 

Por favor introduzca el Bearer Token de Twitter [twitter_token]: 
Introduce una fecha (AAAA-MM-DD):
[Déjalo en blanco si quieres que se recopilen *TODOS*
los tweets ó introduce 'continue' si quieres que el bot se
comporte como de costumbre (comprobando la fecha del
último post de la cuenta del Fediverso)]  
Usando fuente RSS. Las siguientes funcionalidades no estarán disponibles: 
- Actualización de perfil
- Tweets fijados
- Encuestas Versión de API no soportada: {} Contenido adjunto ha excedido el límite configurado ({}) Archivos adjuntos: {}. El límite de archivos adjuntos multimedia para la instancia de destino es {}. Ignorando el resto... Intentando adquirir el bloqueo {} en {} Intentando liberar el bloqueo {} en {} Variable de bot en perfil de destino ({}) difiere de tu configuración. Actualizándola a {}…  Bot para replicar una o varias cuentas de Twitter en Pleroma/Mastodon. No se pudo expandir la URL {}: {} No se pudo expandir la URL: {} Fijado actualmente:	{} Modo de depuración activado Error mientras subiendo contenido:	{} Se produjo una excepción Se produjo una excepción
Código de error 422
(Entidad no procesable)
Por favor compruebe que el texto de biografía o el texto de los campos de metadatos
no se muy largo. Se ha producido una excepción
Contenido no encontrado (404)
{tweet} - {media_url}
Ignorando el adjunto y continuando... Se ha producido una excepción
Tamaño demasiado grande:
Nombre de fichero: {file}
Tamaño: {size}MB
Considere aumentar el límite de
 tamaño de adjuntos para su instancia Se produjo una excepción
Entidad no procesable
{error}
Archivo: {file} Se produjo una excepción para este usuario, omitiendo... Tamaño de fichero: {}MB No se ha encontrado el archivo con el ID del anterior post fijado. Revisando últimos posts... Recopilando tweets...  Recopilando tweets...{} Dándose por vencido, la referencia está demasiado anidada ¿Desde cuándo deberíamos recopilar los tweets de la cuenta de Twitter? Ignorando adjunto y continuando... La instancia parece ser de tipo Misskey ฅ^•ﻌ•^ฅ La respuesta de la instancia no ha podido ser interpretada {} Formato inválido en forceDate, use "AAAA-MM-DD" Parece que pleroma-bot está ejecutándose por primera vez para este usuario: {} Bloqueo {} adquirido en {} Bloqueo {} no adquirido en {}, esperando {} segundos ... Bloqueo {} liberado en {} Mastodon no puede adjuntar un vídeo a un post que ya contiene imágenes, omitiendo vídeo adjunto...  Mastodon no soporta nombres para mostrar de más de 30 caracteres, truncándolo e intentándolo de nuevo... Mastodon no soporta texto enriquecido. Desactivándolo... Mastodon sólo admite {} vídeo/s por post, sin elementos multimedia mixtos. Ya se ha alcanzado el máximo de elementos multimedia, omitiendo el resto...  Mastodon solo soporta {} video/s por cada post. Ya se ha alcanzado el máximo de elementos multimedia, omitiendo el resto...  ¿Contenido no disponible en tu ubicación? (403) Omitiendo... {tweet} - {media_url}  Varios usuarios de Twitter definidos para una cuenta de Fediverso, omitiendo la actualización de perfil y tweet fijado. Varios usuarios de Twitter, omitiendo actualizado de perfil ¡No se ha definido la URL de Pleroma en la configuración! [pleroma_base_url] No se han encontrado posts en la cuenta de Fediverso objetivo No se han encontrado posts en la cuenta de Fediverso objetivo Post fijado no encontrado. Dejamos de intentar el desfijado... No se ha encontrado el archivo con el ID del anterior post fijado. Revisando últimos posts... Fijando post:	{} Publicando en Misskey	{} Publicando en Pleroma	{} El texto del post es más largo que el permitido ({}), truncando... Procesando tweets...  Fijado anteriormente:	{} Procesando tweets...  Procesando usuario:	{} Aumentando max_tweets al valor máximo admitido Se ha superado el límite al utilizar un token de invitado. Reintentando con un proxy... Se ha superado el límite al utilizar un token de invitado. Actualizando token y reintentando... Se ha superado el límite al utilizar un token de invitado. Reintentando con un proxy... Límite excedido. 0 de {} peticiones restantes hasta {} UTC Reblog en Pleroma	{} HTTP 404 recibido al obtener un tweet. ¿Se ha eliminado? Omitiendo... Esperando {} segundos... Software en la instancia objetivo ({}) no reconocido. Usando API de tipo Pleroma como alternativa No todos los tokens OAuth 1.0a han sido encontrados. Usando autenticación de aplicación en su lugar La instancia objetivo es Mastodon... El bloqueo del fichero '{}' no pudo ser adquirido. ¿Hay otra instancia de pleroma-bot en ejecución? Tiempo de espera excedido al intentar adquirir el bloqueo {} en {} El número de campos de metadatos no puede ser superior a 4.
Se han introducido {}. Saliendo... Intentando con {} Tweet ya publicado en Misskey: {} - {}. Omitiendo para evitar duplicados... Tweet ya publicado en Pleroma::	{} - {}. Omitiendo para evitar duplicados... No se han podido recopilar los tweets. ¿Está la cuenta protegida? Si lo está, necesita proporcionar los siguientes valores de OAuth 1.0a en la configuración:
 - consumer_key 
 - consumer_secret 
 - access_token_key 
 - access_token_secret Desfijado:	{} Desfijando anterior:	{} Actualizando perfil:	{} Visibilidad introducida no soportada. Valores válidos: {} application_name no funcionará en Misskey ฅ^ዋ⋏ዋ^ฅ ruta de configuración: {} filtrando Pleroma posts con nombre de aplicación {}, longitud: {} fuerza una fecha específica de comienzo para la recopilación de tweets. El valor de twitter_username (FORCEDATE) puede ser introducido para forzar la fecha de inicio de recopilación sólo para ese usuario específico del archivo de configuración. En lugar de twitter_username se puede proporcionar una fecha (AAAA-MM-DD) para forzar esa fecha en *todos* los usuarios El valor de max_tweets debe estar entre 10 y 3200. max_tweets: {} número de hilos a usar cuando procesando tweets sólo aplica a modo daemon. Frecuencia con la que correr el programa de fondo (en minutos). Por defecto es 60 minutos. ruta del fichero de configuración (config.yml) a usar e interpretar. Si no se especifica, se intentará usar el del directorio de trabajo actual. ruta del fichero de bloqueo (pleroma_bot.lock) para prevenir colisiones  con múltiples instancias del bot. Por defecto se creará  en la ruta del archivo de configuración. ruta del fichero de log (error.log) a escribir. Si no se especifica, se intentará usar la ruta en la que se encuentra el fichero de configuración ruta del fichero de archivo de Twitter (zip) a usar para publicar tweets. correr en modo daemon. Por defecto será relanzado cada 60 minutos. Puede controlar la frecuencia con --pollrate omite la actualización de perfil en la cuenta del Fediverso (imagen de fondo, imagen de perfil, biografía, etc.) omite las validaciones de la primera ejecución tweets recopilados: 	 {} carpeta temporal de tweets: {} tweets a publicar: 	 {} 