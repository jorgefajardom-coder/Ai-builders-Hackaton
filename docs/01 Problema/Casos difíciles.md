---
tags: [problema]
---
# Casos difíciles

| # | Caso | Por qué es difícil | Cómo lo manejamos | Caso de prueba |
|---|---|---|---|---|
| H1 | **Rutas inexistentes** y métodos no permitidos | Los frameworks responden solos (404/405 propios, redirects por `/` final) y eso rompe la paridad | Un *catch-all* propio: nosotros decidimos cada respuesta, el framework no decide nada | T-404, T-405, T-slash |
| H2 | **Estado y orden** | La misma request responde distinto según el historial | Fuzzer de *secuencias* (no solo requests sueltos) + modelo de estado explícito en la spec | T-seq-* |
| H3 | **No determinismo** (IDs, timestamps, aleatoriedad) | La comparación literal falla aunque la lógica sea correcta | Detectarlo repitiendo la misma secuencia 2+ veces tras reset; si es determinista tras reset (p. ej. IDs secuenciales), replicarlo exacto; si no, normalizar en la comparación y documentarlo | T-det |
| H4 | **Autenticación**: sin token, token mal formado, otro token, `Bearer` en minúsculas | Cada variante puede producir un error distinto, y `/__reset` debe imitar al original con token ajeno | Matriz de variantes de auth × rutas en el fuzzer | T-auth-* |
| H5 | **Cuerpos malformados**: JSON inválido, tipos incorrectos, campos faltantes o extra, cuerpo vacío, `Content-Type` incorrecto | Los errores de validación del original tienen mensajes específicos que hay que copiar letra por letra | Fuzzer de mutaciones sobre cuerpos válidos | T-body-* |
| H6 | **Detalles de formato**: orden de claves JSON, espacios, salto de línea final, encoding, `Content-Type` exacto | La comparación byte a byte los detecta; los serializadores por defecto los cambian | Serializar a mano igualando el formato observado; medir paridad estricta y normalizada | T-format |
| H7 | **Bugs del original** | El brief exige replicarlos ("incluidos sus errores"), aunque parezcan incorrectos | Nunca "corregir": si se observa, se replica y se registra en Rarezas de la [[Especificación]] | T-bug-* |
| H8 | **Límites**: strings largos, números grandes o negativos, unicode, listas vacías, paginación | Los casos borde son donde viven los bugs y donde el set oculto probablemente insiste | Valores frontera en el fuzzer | T-edge-* |
| H9 | **Cobertura desconocida** | No sabemos cuántas rutas o comportamientos hay: lo que no sondeemos no lo replicamos | Descubrimiento sistemático (wordlist de rutas, métodos, mensajes de error que filtren pistas) + métrica de cobertura | — |
| H10 | **Incidente a mitad del día** | El original podría cambiar de comportamiento | Corpus versionado con timestamp: re-correr el fuzzer y hacer diff contra el corpus anterior detecta qué cambió en minutos | → [[Incidente]] |
