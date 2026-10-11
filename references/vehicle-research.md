# Suzuki Swift híbrido solicitado: referencias verificadas

Consulta: 11 de octubre de 2026. Las descargas HTTPS siguientes respondieron HTTP 200; se conservaron originales en `official/` durante la investigación. Esa carpeta y los materiales de terceros de `vendor/` se excluyen del repositorio público; los nombres de archivo de este informe documentan las fuentes consultadas y sus enlaces permiten acceder a los originales. Se usa el Swift Hybrid de carrocería actual comercializado por Suzuki Chile durante 2026, con exterior GLX Plus japonés, como referencia de modelado. No se usa Swift Sport ni la carrocería de generación anterior.

## Evidencia del vehículo comercializado en 2026

1. [Suzuki Chile: Swift Hybrid](https://www.suzuki.cl/vehiculo/swift-hybrid/) — página comercial vigente consultada. Ofrece variantes **1.2 GL, GL CVT, GLX Plus y GLX Plus CVT**, motor Mild Hybrid Z12E de 1,2 litros. Las fotos del diseño exterior muestran carrocería moderna con manillas traseras en las puertas, parrilla ovalada debajo del emblema del capó y techo con pilares oscurecidos. Original: `official/swift_hybrid_chile.html`.
2. [Suzuki suma nueva versión del Swift Hybrid](https://www.suzuki.cl/blog/suzuki-suma-nueva-version-del-swift-hybrid/) — **1 de septiembre de 2026**. Confirma llegada de **GLX Plus desde Japón**, nuevas llantas de aleación aro16 y comercialización del Swift Hybrid en Chile en 2026; publica 3.146 ventas en los primeros siete meses de 2026. Original: `official/glx_plus_article.html`.
3. [Ficha técnica Suzuki Chile](https://www.suzuki.cl/media/wmwl3mq3/suzuki_swift-hybrid_ficha-tecnica_web.pdf) — documento oficial descargado; código impreso **FUM 09/26**. Es un PDF de imagen: se conserva en `official/suzuki_swift-hybrid_ficha-tecnica_web.pdf`, render de lectura `official/swift_ficha.png`; el texto OCR es auxiliar y no reemplaza la lectura de tabla.
4. [Global Suzuki, Swift](https://www.globalsuzuki.com/automobile/lineup/swift/) — confirma líneas de hombros redondeadas, pasos de rueda ensanchados, parrilla ovalada metálica negra y sistema SHVS Mild Hybrid. La propia página advierte que sus imágenes corresponden a especificación europea; se cruzaron visualmente con fotos Chile. Original: `official/global_swift.html`.
5. [Suzuki Introduces the All-New Swift](https://www.globalsuzuki.com/globalnews/2023/1206.html) — **6 de diciembre de 2023**, presentación oficial de la carrocería actual, ventas CVT en Japón desde 13 de diciembre 2023 y manual desde 17 de enero 2024; motor Z12E. Sus imágenes y diseño coinciden con la actual oferta Chile 2026. Original: `official/swift_launch2023a.html`.

**Alcance de la identificación:** hay evidencia oficial directa del Swift Hybrid y GLX Plus vendido en Chile en2026 y su exterior actual. Las fuentes no publican un plano CAD de fábrica ni una certificación por VIN/año modelo de un automóvil particular. El modelo imprimible es una interpretación original de esa carrocería basada en fotos y dimensiones oficiales; no corresponde llamarlo réplica CAD de fábrica exacta.

## Dimensiones oficiales y escala

Lectura visual de la ficha, unidades milímetros:

| Parámetro | GL MT / GL CVT | GLX MT Plus / GLX CVT Plus | A 60 mm, exterior GLX |
|---|---:|---:|---:|
| Largo | 3.860 | 3.860 | 60,00 |
| Ancho carrocería | 1.735 | 1.735 | 26,969 |
| Alto | 1.520 | 1.485 | 23,083 |
| Distancia entre ejes | 2.450 | 2.450 | 38,083 |
| Rodada delantera | 1.525 | 1.520 | 23,627 |
| Rodada trasera | 1.530 | 1.520 | 23,627 |
| Despeje mínimo | 145 | 115 | 1,788 |
| Neumáticos | 165/80R14 | 185/55R16 | Ø9,480 calculado |

Escala de carrocería: **1:64,3333**. La relación del diámetro teórico del neumático GLX resulta de 16×25,4 + 2×185×0,55 = 609,9 mm. Espejos no deben suponerse incluidos en los 1.735 mm de ancho de carrocería. La argolla agrega longitud fuera de la escala del auto, según los parámetros ya aprobados de la sujeción.

## Rasgos que deben conservarse en una miniatura FDM

- Hatchback de 5 puertas de carrocería actual; capó corto y redondeado, techo compacto de curva suave, parte trasera vertical.
- Línea horizontal envolvente del capó/hombro, distintiva del diseño presentado en 2023/24.
- Parrilla central ovalada con panal; emblema Suzuki separado por arriba de la parrilla; entrada inferior ancha y baja.
- Faros angulares con contorno DRL tipo C; no faros grandes verticales de modelos antiguos.
- Manillas de las puertas traseras **en la chapa**, visibles debajo de la línea de cintura; no escondidas en el pilar C.
- Ventanas laterales separadas por pilar B, marco negro, pilar C oscuro que sugiere techo flotante.
- Luces traseras exteriores casi cuadradas, esquinas redondeadas y gráficos C; luneta y limpiaparabrisas del portón, hueco placa bajo en parachoques.
- Llantas GLX Plus de 16 pulgadas con cinco conjuntos de radios dobles, pasos de rueda pronunciados, pequeño spoiler de techo. Según ficha, GLX Plus incluye faldón lateral; no añadir grandes faldones, difusor o doble escape Sport.
- Detalles minúsculos se deben engrosar/representar como relieve para boquilla de 0,4 mm. El color azul/techo negro de fotos es referencia visual; el STL monomaterial no codifica pintura.

## Archivos visuales útiles

`official/front_side_rear.png` reúne frontal, lateral, trasera y lateral elevada. Las vistas individuales `global_swift_view_01.png`, `_10.png`, `_19.png`, `_28.png` son composiciones de las capas públicas de carrocería y ruedas del visor oficial (875×525px). `_05`, `_14`, `_23`, `_32` agregan tres cuartos.

Procedencia verificable del visor:

- [Página visor 360° oficial](https://www.globalsuzuki.com/automobile/lineup/swift/viewer/large/main.html)
- [Lista variantes pública](https://www.globalsuzuki.com/automobile/lineup/swift/viewer/assets/setting/grade_list.json)
- [Relación capas GLX](https://www.globalsuzuki.com/automobile/lineup/swift/viewer/assets/setting/GLX/GLX_materials.json)
- Ejemplo frontal: [carrocería01](https://www.globalsuzuki.com/automobile/lineup/swift/viewer/large/materials/EXT-GRD_GLX-BG_A-BC_E6L/EXT-GRD_GLX-BG_A-BC_E6L_01.jpg) y [ruedas01](https://www.globalsuzuki.com/automobile/lineup/swift/viewer/large/materials/EXT-WH_001-BG_A/EXT-WH_001-BG_A_01.png).

El visor utiliza imágenes 2D, no un archivo 3D libre. Las fotografías y capas siguen siendo propiedad de Suzuki; se conservan como referencias de investigación con atribución, sin afirmar que tengan licencia libre para redistribución comercial.

Fotos oficiales Chile:

- [Frontal tres cuartos](https://www.suzuki.cl/media/ahsook2l/suzuki_swift_japo_banner-galeria-exterior_4000x2667_7.webp)
- [Frontal](https://www.suzuki.cl/media/c2hdgeek/suzuki_swift_japo_banner-galeria-exterior_4000x2667_6.webp)
- [Lateral trasero y manilla trasera](https://www.suzuki.cl/media/loyhchd1/suzuki_swift_japo_banner-galeria-exterior_4000x2667_3.webp)
- [Lateral delantero](https://www.suzuki.cl/media/ooqn4nlq/suzuki_swift_japo_banner-galeria-exterior_4000x2667_5.webp)
- [Detalle llanta](https://www.suzuki.cl/media/fdbeyov1/suzuki_swift_japo_banner-galeria-exterior_4000x2667_4.webp)

Las imágenes se descargaron desde las mismas rutas con opciones `rmode=pad&format=webp` de la página oficial.
