---
tags: [referencia]
---
# Cómo diseñaron la prueba

| # | Característica | Implicación para nosotros | Dónde lo cubrimos |
|---|---|---|---|
| 01 | Pruebas del mismo tipo que usan laboratorios como Anthropic u OpenAI para contratar | Evalúan criterio de ingeniería, no solo que funcione: decisiones explícitas, medición y la capacidad de explicarlo | [[Decisiones]] · [[Preguntas probables]] |
| 02 | Un brief ambiguo, como en la vida real | La ambigüedad es intencional. Cada hueco del brief se convierte en un supuesto escrito, con su razón y qué pasa si es falso. No nos quedamos esperando respuestas | [[Supuestos y alcance]] |
| 03 | Un set de evaluaciones oculto que corre sobre algo que no han visto | Generalizar, no sobreajustar a nuestros ejemplos. Respetar el formato de entrada/salida al pie de la letra. Fallar de forma controlada (nunca crashear: devolver algo válido) | [[Plan de evaluación]] · [[Entrega]] |
| 04 | Un incidente a mitad del día, porque en producción las cosas cambian sin avisar | Diseñar para el cambio: configuración fuera del código, componentes desacoplados, evals que se corren en un comando para detectar regresiones. Documentar el incidente al vivo | [[Incidente]] · [[Arquitectura]] |

## Principios de diseño que salen de aquí
1. **Supuestos explícitos > preguntas abiertas.** Si el brief no lo dice, decidimos, lo escribimos y seguimos.
2. **Robustez antes que brillantez.** Una respuesta válida y mediocre es mejor que un crash ante el set oculto.
3. **Todo configurable.** Modelo, prompts, rutas y umbrales se definen en config o env, no hardcodeados.
4. **Evals en un comando.** Así, después del incidente, sabemos en minutos qué se rompió.
5. **Cada componente reemplazable.** Si el incidente cambia una fuente de datos o una API, se toca un solo módulo.
